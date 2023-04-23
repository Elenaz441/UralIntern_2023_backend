

def upload_to(instance, filename: str):
    """ Установливает имя для загруженного изображения в User models.py
    :param instance: Экземпляр объекта, для которого устанавливается изображение
    :param filename: Имя файла
    :return: Строка с именем файла
    """
    ext = filename.split('.')[-1]
    return f'photos/user{instance.id}.{ext}'

