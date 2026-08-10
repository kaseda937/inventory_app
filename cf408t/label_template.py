A4_W_MM = 210
A4_H_MM = 297

LABEL_W_MM = 105
LABEL_H_MM = 148.5

COLS = 2
ROWS = 2
LABELS_PER_PAGE = COLS * ROWS

MARGIN_MM = 5


def format_qr_csv(product_code: str, lot: str, expiry: str, qty: int, row_num: int = 0, slip_number: str = "") -> str:
    return f"{product_code},{lot},{expiry},{qty},{row_num},{slip_number}"


def format_expiry_display(expiry: str) -> str:
    """ラベル面に印字する使用期限の表記。QRの中身(yyyy-mm-dd)は変更しない。

    "2029-07-20" -> "2029年7月20日"。想定外の形式はそのまま返す。
    """
    parts = expiry.split("-")
    if len(parts) != 3:
        return expiry
    try:
        y, m, d = (int(p) for p in parts)
    except ValueError:
        return expiry
    return f"{y}年{m}月{d}日"
