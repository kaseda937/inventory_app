ESC = b"\x1b"


def _esc(cmd: str) -> bytes:
    return ESC + cmd.encode("ascii")


def job_start() -> bytes:
    return _esc("A")


def job_end(copies: int = 1) -> bytes:
    return _esc(f"Q{copies}") + _esc("Z")


def paper_size(height_mm: int, width_mm: int) -> bytes:
    v = f"{height_mm * 10:05d}"
    h = f"{width_mm * 10:04d}"
    return _esc(f"A1V{v}H{h}")


def paper_thermal() -> bytes:
    return _esc("ID00WK")


def text_item(v: int, h: int, text: str, font: str = "0201", rotation: str = "00") -> bytes:
    data = b""
    data += _esc("%0")
    data += _esc(f"V{v:04d}")
    data += _esc(f"H{h:04d}")
    data += _esc(f"P{rotation}")
    data += _esc(f"L{font}")

    encoded = text.encode("cp932")
    has_multibyte = any(b > 0x7F for b in encoded)
    if has_multibyte:
        data += _esc("KD") + encoded + b"\x5c"
    else:
        data += encoded + b"\x5c"
    return data


def qr_code(v: int, h: int, data_str: str, cell_size: int = 5, error_level: str = "Q") -> bytes:
    data = b""
    data += _esc("%0")
    data += _esc(f"V{v:04d}")
    data += _esc(f"H{h:04d}")
    data += _esc("P00")
    data += _esc(f"2D30,{error_level},{cell_size:02d},1,0")

    encoded = data_str.encode("ascii")
    byte_len = f"{len(encoded):04d}"
    data += _esc(f"DN{byte_len},") + encoded
    return data


def build_label(
    height_mm: int,
    width_mm: int,
    text_items: list[tuple[int, int, str]],
    qr_v: int,
    qr_h: int,
    qr_data: str,
    qr_cell_size: int = 5,
    qr_error_level: str = "Q",
    copies: int = 1,
) -> bytes:
    buf = b""
    buf += job_start()
    buf += paper_size(height_mm, width_mm)
    buf += paper_thermal()

    buf += qr_code(qr_v, qr_h, qr_data, qr_cell_size, qr_error_level)

    for v, h, txt in text_items:
        buf += text_item(v, h, txt)

    buf += job_end(copies)
    return buf
