class ResponseStatusCodeExeption(Exception):
    """Исключение статауса ответа от сервера"""
    pass

class ResponseIsDictException(Exception):
    """Исключение проверки типа данных ответа API"""
    pass

class SendMessageException(Exception):
    """Исключение отправки сообщения"""
    pass
