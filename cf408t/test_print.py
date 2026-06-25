import os
import tempfile
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

from . import label_template

PRINT_DPI = 300
MM_TO_PX = PRINT_DPI / 25.4

LABEL_W_MM = label_template.LABEL_W_MM
LABEL_H_MM = label_template.LABEL_H_MM
MARGIN_MM = label_template.MARGIN_MM

A4_W_MM = label_template.A4_W_MM
A4_H_MM = label_template.A4_H_MM

FONT_SIZE_MM = 3.5
LINE_GAP_MM = 1.5


def _mm(mm: float) -> int:
    return int(mm * MM_TO_PX)


def _try_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/msgothic.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/YuGothM.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def render_label(product_code: str, lot: str, expiry: str, qty: int, row_num: int = 0, qr_cell_size: int = 5) -> Image.Image:
    w, h = _mm(LABEL_W_MM), _mm(LABEL_H_MM)
    margin = _mm(MARGIN_MM)
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)

    font_size_px = _mm(FONT_SIZE_MM)
    font = _try_font(font_size_px)
    line_h = font_size_px + _mm(LINE_GAP_MM)
    text_block_h = line_h * 2

    printable_w = w - margin * 2
    printable_h = h - margin * 2
    qr_available_h = printable_h - text_block_h - _mm(2)
    qr_side = min(printable_w, qr_available_h)

    qr_data = label_template.format_qr_csv(product_code, lot, expiry, qty, row_num)
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=1, border=0)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    modules = qr_img.width
    box = qr_side // modules
    qr_actual = box * modules
    qr_img = qr_img.resize((qr_actual, qr_actual), Image.NEAREST)

    qr_x = (w - qr_actual) // 2
    qr_y = margin
    img.paste(qr_img, (qr_x, qr_y))

    col_w = printable_w // 2
    text_y = qr_y + qr_actual + _mm(2)

    row1 = [
        (margin, f"商品ｺｰﾄﾞ: {product_code}"),
        (margin + col_w, f"ﾛｯﾄ: {lot}"),
    ]
    row2 = [
        (margin, f"使用期限: {expiry}"),
        (margin + col_w, f"入荷数: {qty}"),
    ]
    for x, text in row1:
        draw.text((x, text_y), text, fill="black", font=font)
    text_y += line_h
    for x, text in row2:
        draw.text((x, text_y), text, fill="black", font=font)

    return img


def compose_a4_pages(items: list[dict], qr_cell_size: int = 5) -> list[Image.Image]:
    labels = []
    for item in items:
        labels.append(render_label(
            item["product_code"], item["lot"], item["expiry"], item["qty"],
            item.get("row_num", 0), qr_cell_size,
        ))

    a4_w, a4_h = _mm(A4_W_MM), _mm(A4_H_MM)
    label_w, label_h = _mm(LABEL_W_MM), _mm(LABEL_H_MM)
    offset_x = _mm(-2)
    pages = []

    for page_start in range(0, len(labels), label_template.LABELS_PER_PAGE):
        page_labels = labels[page_start:page_start + label_template.LABELS_PER_PAGE]
        page = Image.new("RGB", (a4_w, a4_h), "white")

        for idx, lbl in enumerate(page_labels):
            col = idx % label_template.COLS
            row = idx // label_template.COLS
            x = col * label_w + offset_x
            y = row * label_h
            page.paste(lbl, (x, y))

        pages.append(page)

    return pages


def print_test(items: list[dict], qr_cell_size: int = 5):
    if not items:
        return

    pages = compose_a4_pages(items, qr_cell_size)

    tmp = tempfile.mkdtemp(prefix="label_test_")
    path = Path(tmp) / "label_test.png"
    pages[0].save(
        str(path),
        dpi=(PRINT_DPI, PRINT_DPI),
        append_images=pages[1:] if len(pages) > 1 else [],
    )

    os.startfile(str(path), "print")
