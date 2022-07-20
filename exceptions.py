class ResponseIsDictException(Exception):
    """Исключение проверки типа данных ответа API"""

class SendMessageException(Exception):
    """Исключение отправки сообщения"""

class RequestAPIException(Exception):
    """Ошибка ответа от API"""

class ListHomeworksIsEmptyExceptions(Exception):
    """За отчетный период изменений нет"""
