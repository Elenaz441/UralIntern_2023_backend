import random
import string


def generate_password():
    """Созадет случайный пароль размерами от 8 до 12 символов из букв латиницы верхнего и нижнего регистра и цифр"""
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    size = random.randint(8, 12)
    return ''.join(random.choice(chars) for x in range(size))


def upload_to(instance, filename: str):
    """ Установливает имя для загруженного изображения в User models.py
    :param instance: Экземпляр объекта, для которого устанавливается изображение
    :param filename: Имя файла
    :return: Строка с именем файла
    """
    ext = filename.split('.')[-1]
    return f'photos/user{instance.id}{generate_password()}.{ext}'

