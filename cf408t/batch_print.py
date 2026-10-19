import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import openpyxl

from . import config, printer, gdi_print, test_print


def read_excel(path: str) -> list[dict]:
    # data_only=True: 数式セルは数式ではなくExcelが保存した計算結果を読む
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = []
    seen_keys = {}
    # 列: A=行番号 B=商品コード C=品名 D=ロット E=使用期限 F=入荷数 G=伝票番号 H=製造年月日
    # H列の製造年月日は読み込まない
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        row_num, row = (row[0] if row else None), row[1:]  # A列（行番号）を分離
        if not row or row[0] is None:
            continue
        slip_number = str(row[5]) if len(row) > 5 and row[5] is not None else ""
        # 行番号はQRに入り、棚卸アプリの重複判定（商品コード+ロット+行番号+伝票番号）に使われるため
        # 空欄・整数以外、および行番号+伝票番号の重複は読み込み時に止める
        if isinstance(row_num, float) and row_num.is_integer():
            row_num = int(row_num)
        elif isinstance(row_num, str) and row_num.strip().isdigit():
            row_num = int(row_num.strip())
        if not isinstance(row_num, int) or isinstance(row_num, bool):
            raise ValueError(
                f"{i + 2}行目の行番号（A列）が空か、整数ではありません。\n"
                "数式で計算している場合は、Excelでファイルを開いて上書き保存してから"
                "読み込んでください（計算結果が保存されていないと読み取れません）。"
            )
        key = (row_num, slip_number)
        if key in seen_keys:
            slip_label = f"伝票番号 {slip_number}" if slip_number else "伝票番号なし"
            raise ValueError(
                f"行番号 {row_num}（{slip_label}）が {seen_keys[key]}行目と{i + 2}行目で重複しています。\n"
                "同じ伝票番号の中では、行番号（A列）を行ごとに異なる番号にしてください。"
            )
        seen_keys[key] = i + 2
        expiry = row[3]
        if expiry is None:
            raise ValueError(
                f"{i + 2}行目の使用期限が空です。\n"
                "数式で計算している場合は、Excelでファイルを開いて上書き保存してから"
                "読み込んでください（計算結果が保存されていないと読み取れません）。"
            )
        if hasattr(expiry, "strftime"):
            expiry = expiry.strftime("%Y-%m-%d")
        else:
            expiry = str(expiry)
        rows.append({
            "row_num": row_num,
            "product_code": str(row[0]),
            "product_name": str(row[1]),
            "lot": str(row[2]),
            "expiry": expiry,
            "qty": int(row[4]),
            "slip_number": slip_number,
        })
    wb.close()
    return rows


class BatchPrintApp:
    def __init__(self):
        self.cfg = config.load()
        self.data: list[dict] = []
        self.printer_name: str = self.cfg.get("printer_name", "")

        self.root = tk.Tk()
        self.root.title("バルク管理ラベル一括発行")
        self.root.geometry("780x520")
        self._build_ui()

    def _build_ui(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill="x", padx=8, pady=8)

        ttk.Button(toolbar, text="Excel読込", command=self._load_excel).pack(side="left", padx=4)
        ttk.Button(toolbar, text="プリンター選択", command=self._select_printer).pack(side="left", padx=4)

        self.printer_label = ttk.Label(toolbar, text=self._printer_display(), font=("", 9))
        self.printer_label.pack(side="left", padx=12)

        ttk.Button(toolbar, text="選択行を印刷", command=self._print_selected).pack(side="right", padx=4)
        ttk.Button(toolbar, text="全件印刷", command=self._print_all).pack(side="right", padx=4)

        columns = ("row", "product_code", "product_name", "lot", "expiry", "qty", "slip_number")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", selectmode="extended")
        headers = {"row": "#", "product_code": "商品コード", "product_name": "品名",
                   "lot": "ロット", "expiry": "使用期限", "qty": "入荷数", "slip_number": "伝票番号"}
        widths = {"row": 40, "product_code": 120, "product_name": 160,
                  "lot": 80, "expiry": 100, "qty": 70, "slip_number": 100}
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor="center" if col in ("row", "qty") else "w")

        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=(0, 8))
        self.tree.pack(fill="both", expand=True, padx=(8, 0), pady=(0, 8))

        self.status = ttk.Label(self.root, text="Excelファイルを読み込んでください", relief="sunken", anchor="w")
        self.status.pack(fill="x", padx=8, pady=(0, 8))

    def _printer_display(self) -> str:
        if self.printer_name:
            return f"プリンター: {self.printer_name}"
        return "プリンター: 未選択"

    def _load_excel(self):
        path = filedialog.askopenfilename(
            title="ロットリストを選択",
            filetypes=[("Excel", "*.xlsx"), ("All", "*.*")],
            initialdir=str(config.CONFIG_PATH.parent),
        )
        if not path:
            return
        try:
            self.data = read_excel(path)
        except Exception as e:
            messagebox.showerror("読込エラー", str(e))
            return

        self.tree.delete(*self.tree.get_children())
        for d in self.data:
            self.tree.insert("", "end", values=(
                d["row_num"], d["product_code"], d["product_name"],
                d["lot"], d["expiry"], d["qty"], d["slip_number"],
            ))

        self.cfg["excel_path"] = path
        config.save(self.cfg)
        self.status.config(text=f"{len(self.data)} 件読み込みました: {path}")

    def _select_printer(self):
        name = printer.select_printer_dialog(self.root, default=self.printer_name)
        if name:
            self.printer_name = name
            self.printer_label.config(text=self._printer_display())
            self.cfg["printer_name"] = name
            config.save(self.cfg)

    def _do_print(self, items: list[dict]):
        if not self.printer_name:
            messagebox.showwarning("プリンター未選択", "先にプリンターを選択してください")
            return
        if not items:
            messagebox.showwarning("対象なし", "印刷するデータがありません")
            return

        from . import label_template
        page_count = (len(items) + label_template.LABELS_PER_PAGE - 1) // label_template.LABELS_PER_PAGE
        if not messagebox.askokcancel("印刷確認",
                f"{len(items)} 枚のラベルを印刷します（A4 {page_count} ページ）\nよろしいですか?"):
            return

        self.status.config(text="印刷中...")
        self.root.update_idletasks()

        try:
            gdi_print.print_items(
                printer_name=self.printer_name,
                items=items,
                qr_cell_size=self.cfg.get("qr_cell_size", 5),
            )
            self.status.config(text=f"{len(items)} 枚のラベル印刷が完了しました（{page_count} ページ）")
        except Exception as e:
            messagebox.showerror("印刷エラー", str(e))

    def _print_all(self):
        self._do_print(self.data)

    def _print_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("未選択", "印刷する行を選択してください")
            return
        items = [self.data[self.tree.index(item)] for item in selected]
        self._do_print(items)

    def _test_print(self):
        if not self.data:
            messagebox.showwarning("対象なし", "先にExcelファイルを読み込んでください")
            return
        selected = self.tree.selection()
        if selected:
            items = [self.data[self.tree.index(item)] for item in selected]
        else:
            items = self.data

        self.status.config(text=f"A4テスト印刷用画像を生成中... ({len(items)} 件)")
        self.root.update_idletasks()

        try:
            test_print.print_test(items, qr_cell_size=self.cfg.get("qr_cell_size", 5))
            self.status.config(text="A4テスト印刷をペイントに送信しました")
        except Exception as e:
            messagebox.showerror("テスト印刷エラー", str(e))

    def run(self):
        self.root.mainloop()


def main():
    app = BatchPrintApp()
    try:  # PyInstaller スプラッシュ画面を閉じる（未frozen時は存在しない）
        import pyi_splash
        pyi_splash.close()
    except ImportError:
        pass
    app.run()


if __name__ == "__main__":
    main()
