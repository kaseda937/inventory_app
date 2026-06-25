import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import openpyxl

from . import config, printer, gdi_print, test_print


def read_excel(path: str) -> list[dict]:
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    rows = []
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if row[0] is None:
            continue
        expiry = row[3]
        if hasattr(expiry, "strftime"):
            expiry = expiry.strftime("%Y-%m-%d")
        else:
            expiry = str(expiry)
        rows.append({
            "row_num": i + 2,
            "product_code": str(row[0]),
            "product_name": str(row[1]),
            "lot": str(row[2]),
            "expiry": expiry,
            "qty": int(row[4]),
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
        ttk.Button(toolbar, text="A4テスト印刷", command=self._test_print).pack(side="right", padx=4)

        columns = ("row", "product_code", "product_name", "lot", "expiry", "qty")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", selectmode="extended")
        headers = {"row": "#", "product_code": "商品コード", "product_name": "品名",
                   "lot": "ロット", "expiry": "使用期限", "qty": "入荷数"}
        widths = {"row": 40, "product_code": 120, "product_name": 180,
                  "lot": 80, "expiry": 100, "qty": 80}
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
                d["lot"], d["expiry"], d["qty"],
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
    app.run()


if __name__ == "__main__":
    main()
