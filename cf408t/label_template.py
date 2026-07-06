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
