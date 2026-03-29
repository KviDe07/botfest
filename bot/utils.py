import secrets
from io import BytesIO

import qrcode
from aiogram.types import BufferedInputFile

from .storage import load_registrations


def generate_reg_code() -> str:
    while True:
        code = secrets.token_hex(3).upper()
        existing = load_registrations()
        if not any(reg.get("reg_code") == code for reg in existing):
            return code


def generate_qr(data: str) -> BufferedInputFile:
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return BufferedInputFile(bio.read(), filename="qr.png")


def normalize_phone(phone: str) -> str | None:
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
    if cleaned.startswith("+") and cleaned[1:].isdigit() and len(cleaned) > 5:
        return cleaned
    return None
