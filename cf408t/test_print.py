import os
import tempfile
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

from . import label_template

PRINT_DPI = 300
MM_TO_PX = PRINT_DPI / 25.4

LABEL_W_MM = label_template.PAPER_W_MM
LABEL_H_MM = label_template.PAPER_H_MM


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
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, w - 1, h - 1], outline="black", width=2)

    qr_data = label_template.format_qr_csv(product_code, lot, expiry, qty, row_num)
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=qr_cell_size, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    max_qr_w = w - _mm(10)
    max_qr_h = h // 2 - _mm(5)
    qr_img.thumbnail((max_qr_w, max_qr_h), Image.LANCZOS)

    qr_x = (w - qr_img.width) // 2
    qr_y = _mm(5)
    img.paste(qr_img, (qr_x, qr_y))

    font_size = max(16, _mm(3))
    font = _try_font(font_size)

    text_y = qr_y + qr_img.height + _mm(3)
    line_h = font_size + _mm(2)
    text_x = _mm(3)

    lines = [
        f"商品ｺｰﾄﾞ: {product_code}",
        f"ﾛｯﾄ: {lot}",
        f"使用期限: {expiry}",
        f"入荷数: {qty}",
    ]
    for line in lines:
        draw.text((text_x, text_y), line, fill="black", font=font)
        text_y += line_h

    return img


def print_test(items: list[dict], qr_cell_size: int = 5):
    if not items:
        return

    labels = []
    for item in items:
        labels.append(render_label(
            item["product_code"], item["lot"], item["expiry"], item["qty"],
            item.get("row_num", 0), qr_cell_size,
        ))

    # ラベルを縦に連結した1枚の画像にする
    total_h = sum(img.height for img in labels)
    max_w = max(img.width for img in labels)
    combined = Image.new("RGB", (max_w, total_h), "white")
    y = 0
    for img in labels:
        combined.paste(img, (0, y))
        y += img.height

    tmp = tempfile.mkdtemp(prefix="label_test_")
    path = Path(tmp) / "label_test.png"
    combined.save(str(path), dpi=(PRINT_DPI, PRINT_DPI))

    # Windows標準の写真印刷ダイアログで開く
    # 「フルページ写真」を選べば用紙いっぱいに拡大印刷される
    os.startfile(str(path), "print")
