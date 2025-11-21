"""QR Code generation utilities."""

import secrets
from functools import lru_cache
from io import BytesIO

import qrcode
from qrcode.image.pil import PilImage


def generate_check_in_token() -> str:
    """
    Генерация уникального токена для check-in.

    Returns:
        str: Безопасный URL-safe токен длиной 32 символа
    """
    return secrets.token_urlsafe(32)


@lru_cache(maxsize=500)
def generate_qr_code_image(data: str) -> bytes:
    """
    Генерация QR-кода в виде PNG изображения.

    Args:
        data: Данные для кодирования в QR-код (обычно check_in_token)

    Returns:
        bytes: PNG изображение QR-кода
    """
    qr = qrcode.QRCode(
        version=1,  # Размер QR-кода (1-40)
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Уровень коррекции ошибок
        box_size=10,  # Размер каждого "пикселя"
        border=4,  # Размер белой рамки (минимум 4)
    )

    qr.add_data(data)
    qr.make(fit=True)

    # Создаем изображение
    img = qr.make_image(fill_color="black", back_color="white", image_factory=PilImage)

    # Конвертируем в bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer.getvalue()
