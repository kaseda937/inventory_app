import json
import sys
from pathlib import Path

DEFAULT_CONFIG = {
    "printer_name": "",
    "qr_cell_size": 5,
    "qr_error_correction": "Q",
    "excel_path": "",
}

if getattr(sys, 'frozen', False):
    CONFIG_PATH = Path(sys.executable).parent / "config.json"
else:
    CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def load() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        return {**DEFAULT_CONFIG, **saved}
    return dict(DEFAULT_CONFIG)


def save(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
