import win32print
import tkinter as tk
from tkinter import ttk, messagebox


def list_printers() -> list[str]:
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    return [p[2] for p in win32print.EnumPrinters(flags)]


def select_printer_dialog(parent: tk.Tk, default: str = "") -> str | None:
    printers = list_printers()
    if not printers:
        messagebox.showerror("エラー", "プリンターが見つかりません", parent=parent)
        return None

    selected = [None]

    dialog = tk.Toplevel(parent)
    dialog.title("プリンター選択")
    dialog.geometry("420x320")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    ttk.Label(dialog, text="使用するプリンターを選択してください:", font=("", 10)).pack(
        padx=16, pady=(16, 8), anchor="w"
    )

    frame = ttk.Frame(dialog)
    frame.pack(fill="both", expand=True, padx=16)

    listbox = tk.Listbox(frame, font=("", 10), selectmode="single")
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    listbox.pack(side="left", fill="both", expand=True)

    for name in printers:
        listbox.insert("end", name)

    if default and default in printers:
        idx = printers.index(default)
        listbox.selection_set(idx)
        listbox.see(idx)
    elif printers:
        listbox.selection_set(0)

    def on_ok():
        sel = listbox.curselection()
        if sel:
            selected[0] = printers[sel[0]]
        dialog.destroy()

    def on_cancel():
        dialog.destroy()

    def on_double_click(event):
        on_ok()

    listbox.bind("<Double-Button-1>", on_double_click)

    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(pady=12)
    ttk.Button(btn_frame, text="OK", width=10, command=on_ok).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="キャンセル", width=10, command=on_cancel).pack(side="left", padx=4)

    parent.wait_window(dialog)
    return selected[0]


def send_raw(printer_name: str, data: bytes):
    h = win32print.OpenPrinter(printer_name)
    try:
        win32print.StartDocPrinter(h, 1, ("SBPL Label", None, "RAW"))
        win32print.StartPagePrinter(h)
        win32print.WritePrinter(h, data)
        win32print.EndPagePrinter(h)
        win32print.EndDocPrinter(h)
    finally:
        win32print.ClosePrinter(h)
