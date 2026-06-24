from . import sbpl

DOTS_PER_MM = 8

# PDラベル P115×W80mm
PAPER_H_MM = 115
PAPER_W_MM = 80

# QRコード配置（ラベル上部・中央寄せ）
QR_V = 40
QR_H = 170

# テキスト配置（QR下部、4行）
TEXT_START_V = 560
TEXT_H = 40
TEXT_LINE_HEIGHT = 80


def format_qr_csv(product_code: str, lot: str, expiry: str, qty: int, row_num: int = 0) -> str:
    return f"{product_code},{lot},{expiry},{qty},{row_num}"


def build(
    product_code: str,
    product_name: str,
    lot: str,
    expiry: str,
    qty: int,
    row_num: int = 0,
    qr_cell_size: int = 5,
    qr_error_level: str = "Q",
    copies: int = 1,
) -> bytes:
    qr_data = format_qr_csv(product_code, lot, expiry, qty, row_num)

    v = TEXT_START_V
    text_items = [
        (v, TEXT_H, f"商品ｺｰﾄﾞ: {product_code}"),
        (v + TEXT_LINE_HEIGHT, TEXT_H, f"ﾛｯﾄ: {lot}"),
        (v + TEXT_LINE_HEIGHT * 2, TEXT_H, f"使用期限: {expiry}"),
        (v + TEXT_LINE_HEIGHT * 3, TEXT_H, f"入荷数: {qty}"),
    ]

    return sbpl.build_label(
        height_mm=PAPER_H_MM,
        width_mm=PAPER_W_MM,
        text_items=text_items,
        qr_v=QR_V,
        qr_h=QR_H,
        qr_data=qr_data,
        qr_cell_size=qr_cell_size,
        qr_error_level=qr_error_level,
        copies=copies,
    )
