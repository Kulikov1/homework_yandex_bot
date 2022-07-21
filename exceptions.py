class SendMessageException(Exception):
    """Исключение отправки сообщения"""

class RequestAPIException(Exception):
    """Ошибка ответа от API"""

class ListHomeworksIsEmptyExceptions(Exception):
    """За отчетный период изменений нет"""

class ResponseStatusException(Exception):
    """Вызывается, если статус ответа от сервера не 200"""
