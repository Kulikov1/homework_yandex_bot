import logging
import os
import time
from http import HTTPStatus

import telegram
import requests

from dotenv import load_dotenv
from exceptions import ResponseStatusCodeExeption, ResponseIsDictException, SendMessageException

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = 1532468150

RETRY_TIME = 5
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Функция отправки сообщения через телеграм бота."""
    chat_id = TELEGRAM_CHAT_ID
    try:
        return bot.send_message(chat_id, message)
    except:
        logging.error('Сообщение %s не отправлено!', message)
        raise SendMessageException(f'Сообщение {message} не отправлено!')
    finally:
        logging.info('Сообщение %s отправлено!', message)



def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API - сервиса Яндекс Практикум."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except:
        logging.error('Ошибка при запросе к основному API:')
    if response.status_code != HTTPStatus.OK:
        logging.error('Статус код не 200!')
        raise ResponseStatusCodeExeption('API не ответил!')
    return response.json()

def check_response(response):
    """Проверяет, что ответ от API корректный и приведен к типам данных Python"""
    homework_list = response['homeworks']
    if homework_list == []:
        raise IndexError('Список домашних работ пуст')
    if isinstance(homework_list, dict):
        raise ResponseIsDictException('Ответ от api вернулся словарем!')
    if isinstance(homework_list, list):
        return homework_list[0]

def parse_status(homework):
    """Bзвлекает из информации о конкретной домашней работе статус этой работы"""
    if 'homework_name' not in homework:
        logging.error('Нет ключа homework_name в ответе API')
        raise KeyError('Статуса нет!')
    if 'status' not in homework:
        logging.error('Нет ключа status в ответе API')
        raise KeyError('Статуса нет!')
    if homework.get('status') not in HOMEWORK_STATUSES:
        raise KeyError('Статус не подходит!')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    verdict = HOMEWORK_STATUSES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения"""
    try:
        return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))
    except:
        logging.critical('Отсутствие обязательных переменных окружения во время запуска бота!')
        raise ValueError('1 или несколько токенов отсутсвуют!')

def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 1654811090
    sended_message = ''
    check_tokens()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            chek = check_response(response)
            message = parse_status(chek)
            send_message(bot, message)
            current_timestamp = response['current_date']
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if sended_message != message:
                send_message(bot, message)
            sended_message = message
            logging.info('Сбой в работе программы: %s', error)
            time.sleep(RETRY_TIME)
        else:
            pass


if __name__ == '__main__':
    main()
