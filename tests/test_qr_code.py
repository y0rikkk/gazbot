"""Tests for QR code generation."""

import pytest
from io import BytesIO
from PIL import Image

from app.core.qr_code import generate_check_in_token, generate_qr_code_image


def test_generate_check_in_token():
    """Тест генерации токена для check-in."""
    token = generate_check_in_token()

    # Проверяем, что токен не пустой
    assert token is not None
    assert len(token) > 0

    # Проверяем, что токены уникальны
    token2 = generate_check_in_token()
    assert token != token2


def test_generate_qr_code_image():
    """Тест генерации QR-кода."""
    data = "test_check_in_token_12345"

    qr_bytes = generate_qr_code_image(data)

    # Проверяем, что получили байты
    assert qr_bytes is not None
    assert isinstance(qr_bytes, bytes)
    assert len(qr_bytes) > 0

    # Проверяем, что это валидное изображение
    image = Image.open(BytesIO(qr_bytes))
    assert image.format == "PNG"
    assert image.size == (330, 330)  # box_size=10 + border=4 -> 33x10 = 330


def test_generate_qr_code_image_caching():
    """Тест кэширования QR-кодов."""
    data = "test_cache_token"

    # Генерируем QR-код дважды с одинаковыми данными
    qr_bytes1 = generate_qr_code_image(data)
    qr_bytes2 = generate_qr_code_image(data)

    # Результаты должны быть одинаковыми благодаря кэшированию
    assert qr_bytes1 == qr_bytes2
