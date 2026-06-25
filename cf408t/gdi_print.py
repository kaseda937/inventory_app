import win32print
import win32ui
import win32con
from PIL import Image, ImageWin

from . import label_template, test_print


def print_pages(printer_name: str, pages: list[Image.Image]):
    hdc = win32ui.CreateDC()
    hdc.CreatePrinterDC(printer_name)

    dpi_x = hdc.GetDeviceCaps(win32con.LOGPIXELSX)
    dpi_y = hdc.GetDeviceCaps(win32con.LOGPIXELSY)

    page_w = int(label_template.A4_W_MM / 25.4 * dpi_x)
    page_h = int(label_template.A4_H_MM / 25.4 * dpi_y)

    hdc.StartDoc("バルク管理ラベル")

    for img in pages:
        hdc.StartPage()

        scale_x = page_w / img.width
        scale_y = page_h / img.height
        scale = min(scale_x, scale_y)

        dst_w = int(img.width * scale)
        dst_h = int(img.height * scale)
        dst_x = (page_w - dst_w) // 2
        dst_y = (page_h - dst_h) // 2

        dib = ImageWin.Dib(img)
        dib.draw(hdc.GetHandleOutput(), (dst_x, dst_y, dst_x + dst_w, dst_y + dst_h))

        hdc.EndPage()

    hdc.EndDoc()
    hdc.DeleteDC()


def print_items(printer_name: str, items: list[dict], qr_cell_size: int = 5):
    pages = test_print.compose_a4_pages(items, qr_cell_size)
    print_pages(printer_name, pages)
