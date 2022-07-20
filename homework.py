import logging
import os
import time
from http import HTTPStatus

import telegram
import requests

from dotenv import load_dotenv
from exceptions import (
    ResponseIsDictException,SendMessageException,
    RequestAPIException, ListHomeworksIsEmptyExceptions
)
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = 1532468150

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Функция отправки сообщения через телеграм бота."""
    try:
        return bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        raise SendMessageException


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API - сервиса Яндекс Практикум."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        logging.info('Запрос к серверу.')
        if response.status_code != HTTPStatus.OK:
            raise Exception('Код ответа от API не 200!')
        return response.json()
    except Exception:
        raise RequestAPIException


def check_response(response):
    """
    Проверяет, что ответ от API корректный.
    А так же, что он приведен к типам данных Python.
    """
#   if "homeworks" not in response:
#        raise KeyError('Ключ homeworks отсутсвуетв в словаре')
    if not any(element in 'homeworks' for element in response):
        raise KeyError('Ключ homeworks отсутсвуетв в словаре')
    homework_list = response['homeworks']
    if homework_list == []:
        raise ListHomeworksIsEmptyExceptions('Изменений в списке домашних работ нет')
    if isinstance(homework_list, list):
        return homework_list[0]
    raise Exception('Response от API не корректный')


def parse_status(homework):
    """Извлекает из конкретной домашней работы статус этой работы."""
    if 'homework_name' not in homework:
        raise KeyError('Нет ключа homework_name в ответе API!')
    if 'status' not in homework:
        raise KeyError('Нет ключа status в ответе API!')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework.get('status') not in HOMEWORK_STATUSES:
        raise KeyError(f'Статус {homework_status} не подходит!')

    verdict = HOMEWORK_STATUSES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    sended_message = ''
    sended_error_message = ''
    check_tokens()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            chek = check_response(response)
            message = parse_status(chek)
            if sended_message!= message:
                send_message(bot, message)
                logging.info('Сообщение %s отправлено!', message)
            sended_message = message
            current_timestamp = response['current_date']
        except SendMessageException:
            logging.error('Бот не может отправить сообщение')
            raise SendMessageException('Бот не может отправить сообщение')
        except RequestAPIException:
            logging.error('Ошибка ответа от API')
            raise RequestAPIException('Ошибка ответа от API')
        except ListHomeworksIsEmptyExceptions:
            logging.info('Изменений в статусе работы нет.')
        except ResponseIsDictException as exc:
            logging.error(exc)
            raise ResponseIsDictException(exc)
        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            if sended_error_message != error_message:
                send_message(bot, error_message)
            sended_error_message = error_message
            logging.error('Сбой в работе программы: %s', error)
            raise Exception(error)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
