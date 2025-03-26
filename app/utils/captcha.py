import os
import time
import uuid
import random
import string
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Tuple, Optional, Any

class CaptchaGenerator:
    """Класс для генерации и проверки CAPTCHA"""

    def __init__(self):
        """Инициализация генератора CAPTCHA"""
        self.captchas = {}  # словарь для хранения сгенерированных капч
        self.captcha_expiration = 600  # срок действия капчи в секундах (10 минут)
        
        # Путь к шрифтам
        self.font_path = os.path.join(os.path.dirname(__file__), 'fonts')
        if not os.path.exists(self.font_path):
            os.makedirs(self.font_path, exist_ok=True)
            
        # Проверяем, есть ли файл шрифта, если нет, используем шрифт по умолчанию
        self.font_file = os.path.join(self.font_path, 'arial.ttf')
        if not os.path.exists(self.font_file):
            # Использовать шрифт по умолчанию из системы
            self.font_file = None

    def generate_captcha(self) -> Dict[str, str]:
        """
        Генерирует новую CAPTCHA и возвращает идентификатор и изображение

        Returns:
            Dict[str, str]: Словарь с captcha_id и изображением в base64
        """
        # Генерируем случайный код капчи (6 символов)
        captcha_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Генерируем уникальный идентификатор
        captcha_id = str(uuid.uuid4())
        
        # Сохраняем код и время создания
        self.captchas[captcha_id] = {
            'code': captcha_code,
            'created_at': time.time()
        }
        
        # Очистка устаревших капч
        self._cleanup_expired_captchas()
        
        # Создаем изображение капчи
        image_base64 = self._generate_captcha_image(captcha_code)
        
        return {
            'captcha_id': captcha_id,
            'image': image_base64
        }

    def verify_captcha(self, captcha_id: str, user_input: str) -> bool:
        """
        Проверяет введенный пользователем код CAPTCHA

        Args:
            captcha_id: Идентификатор CAPTCHA
            user_input: Введенный пользователем код

        Returns:
            bool: True, если код верный и не истек срок действия, иначе False
        """
        if not captcha_id or not user_input:
            return False
        
        # Получаем данные капчи по идентификатору
        captcha_data = self.captchas.get(captcha_id)
        if not captcha_data:
            return False
        
        # Проверяем срок действия
        if time.time() - captcha_data['created_at'] > self.captcha_expiration:
            # Удаляем устаревшую капчу
            del self.captchas[captcha_id]
            return False
        
        # Сравниваем код (без учета регистра)
        is_valid = user_input.upper() == captcha_data['code']
        
        # Удаляем капчу после проверки (одноразовое использование)
        del self.captchas[captcha_id]
        
        return is_valid

    def _cleanup_expired_captchas(self) -> None:
        """Удаляет устаревшие CAPTCHA из хранилища"""
        current_time = time.time()
        expired_ids = [
            captcha_id for captcha_id, data in self.captchas.items()
            if current_time - data['created_at'] > self.captcha_expiration
        ]
        
        for captcha_id in expired_ids:
            del self.captchas[captcha_id]

    def _generate_captcha_image(self, code: str) -> str:
        """
        Создает изображение с CAPTCHA кодом

        Args:
            code: Код CAPTCHA для отображения

        Returns:
            str: Изображение в формате base64
        """
        # Создаем изображение
        width, height = 200, 80
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Добавляем шум (точки)
        for _ in range(1000):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            draw.point((x, y), fill=(
                random.randint(0, 200),
                random.randint(0, 200),
                random.randint(0, 200)
            ))
        
        # Добавляем линии для шума
        for _ in range(10):
            x1 = random.randint(0, width - 1)
            y1 = random.randint(0, height - 1)
            x2 = random.randint(0, width - 1)
            y2 = random.randint(0, height - 1)
            draw.line((x1, y1, x2, y2), fill=(
                random.randint(0, 200),
                random.randint(0, 200),
                random.randint(0, 200)
            ), width=2)
        
        # Устанавливаем шрифт
        try:
            font = ImageFont.truetype(self.font_file, 45) if self.font_file else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
        
        # Рисуем текст
        text_width = width / len(code)
        for i, char in enumerate(code):
            # Случайное смещение для каждого символа
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            # Случайный цвет
            color = (
                random.randint(0, 100),
                random.randint(0, 100),
                random.randint(0, 100)
            )
            # Случайный угол наклона
            angle = random.randint(-30, 30)
            
            # Создаем изображение для одного символа
            char_img = Image.new('RGBA', (60, 60), color=(255, 255, 255, 0))
            char_draw = ImageDraw.Draw(char_img)
            char_draw.text((30, 30), char, font=font, fill=color)
            
            # Поворачиваем изображение символа
            rotated = char_img.rotate(angle, expand=1)
            
            # Вставляем символ в основное изображение
            pos_x = int(i * text_width) + offset_x
            pos_y = int(height / 3) + offset_y
            image.paste(rotated, (pos_x, pos_y), rotated)
        
        # Конвертируем изображение в base64
        buffer = BytesIO()
        image.save(buffer, format='JPEG')
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/jpeg;base64,{img_str}"


# Создаем глобальный экземпляр для использования в приложении
captcha = CaptchaGenerator() 