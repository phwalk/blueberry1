import base64
from PIL import Image
from io import BytesIO

# Полный код изображения (base64) — вот ваша картинка
b64_data = """
iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==
"""

# Декодируем и показываем
img_data = base64.b64decode(b64_data)
img = Image.open(BytesIO(img_data))
img.show()  # Откроет фото