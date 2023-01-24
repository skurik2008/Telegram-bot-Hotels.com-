import logging
import requests
import json
from datetime import datetime
import utils
import os
import database


def realization(bot, data=None):
    """
    Функция первого порядка, содержит функции для пошаговой реализации команды /highprice
    :param bot: бот
    :param data: объект класса DataSearch модуля models,
                в который в результате реализации функции вносятся значения-параметры для итогового вывода-результата команды
    :return: функцию get_city (функция следующего шага)
    """
    def get_city(message):
        """
        Функция второго порядка завершает запрос у пользователя названия города и
        запрашивает уточнение названия города или дату заезда.
        Запускает следующую функцию-шаг в зависимости от входящего сообщения пользователя
        :param message: блок данных по последнему входящему сообщению пользователя
        """
        try:
            data.city_name = message.text
            response = requests.request("GET", os.getenv('url_id_city'), headers=json.loads(os.getenv('headers')), params={"query": data.city_name})
            res = json.loads(response.text)
            name_city = res.get('suggestions')[0].get('entities')[0].get('name')
            if res.get('moresuggestions') == 0:
                new_message = 'Я не нашел такого города! Попробуйте еще раз!'
                utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_city, repeat_step=True)
                return
            elif name_city != message.text:
                data.city_name = name_city
                new_message = f"Мы ищем этот город - {name_city}?"
                utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_repeat, repeat_step=True)
                return
        except Exception as e:
            new_message = 'Что-то с названием города у нас не складывается! Попробуйте ввести точнее!'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_city, repeat_step=True)
        else:
            new_message = 'Введите дату заезда (число, месяц, год через пробел)\nНапример, 5 6 2022'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_check_in, repeat_step=False)

    def get_repeat(message):
        """
        Функция второго порядка. Запускается в случае уточняющего вопроса по названию города со стороны бота.
        Запускает повтор либо запрашивает дату заезда и запускает следующую функцию-шаг.
        :param message:блок данных по последнему входящему сообщению пользователя
        """
        if message.text.lower() == 'да':
            new_message = 'Введите дату заезда (число, месяц, год) через пробел\nНапример, 5 6 2022'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_check_in, repeat_step=False)
        elif message.text.lower() == 'нет':
            new_message = 'Попробуйте вновь ввести название города'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_city, repeat_step=False)
        else:
            new_message = 'Мне нужен ответ: Да/Нет'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_repeat, repeat_step=True)

    def get_check_in(message):
        """
        Функция второго порядка завершает запрос у пользователя даты заезда в отель,
        запрашивает дату выезда и запускает следующую функцию-шаг
        :param message: блок данных по последнему входящему сообщению пользователя
        """
        current_date = datetime.now()
        try:
            dl = list(map(int, message.text.split(' ')))
            y, m, d = dl[2], dl[1], dl[0]
            check_in = datetime(y, m, d)
            if check_in < current_date:
                new_message = 'Вы возвращаетесь в прошлое?\nВведите дату заезда еще раз'
                utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_check_in, repeat_step=True)
                return
        except Exception as e:
            new_message = 'Ошибка ввода даты! Попробуйте еще раз!' \
                           '\nНапоминаю правило ввода: число, месяц, год через пробел!'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_check_in, repeat_step=True)
        else:
            data.check_in = check_in
            new_message = 'Введите дату выезда (число, месяц, год) через пробел\nНапример, 5 6 2022'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_check_off, repeat_step=False)

    def get_check_off(message):
        """
        Функция второго порядка завершает запрос у пользователя даты выезда из отеля,
        запрашивает количество отелей и запускает следующую функцию-шаг
        :param message: блок данных по последнему входящему сообщению пользователя
        """
        try:
            dl = list(map(int, message.text.split(' ')))
            y, m, d = dl[2], dl[1], dl[0]
            check_off = datetime(y, m, d)
            if check_off < data.check_in:
                new_message = 'Дата выезда должна быть позже даты заезда!\nВведите дату заезда еще раз'
                utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_check_off, repeat_step=True)
                return
        except Exception as e:
            new_message = 'Неправильный ввод даты! Попробуйте еще раз!' \
                           '\nНапоминаю правило ввода: число, месяц, год через пробел!'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_check_off, repeat_step=True)
        else:
            data.check_off = check_off
            new_message = 'Сколько отелей показать (не больше 10)'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_photo, repeat_step=False)

    def get_photo(message):
        """
        Функция второго порядка завершает запрос у пользователя количества отелей для показа,
        запрашивает показ фото отелей и запускает следующую функцию-шаг
        :param message: блок данных по последнему входящему сообщению пользователя
        """
        try:
            if int(message.text) > 10 or int(message.text) <= 0:
                if int(message.text) > 10:
                    new_message = 'Я же просил не больше 10! Попробуем еще раз!\nСколько отелей показать?'
                elif int(message.text) <= 0:
                    new_message = 'Меньше ноля и ноль тоже не подходит! Попробуем еще раз!\nСколько отелей показать?'
                utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_photo, repeat_step=True)
                return
        except Exception as e:
            new_message = 'Введите цифру!'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_photo, repeat_step=True)
        else:
            data.numbers_hotels = message.text
            new_message = 'Фото отеля показать?'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_number_photo, repeat_step=False)

    def get_number_photo(message):
        """
        Функция второго порядка. Завершает работу команды /highprice в случае отказа пользователя от показа фото отелей
        либо запрашивает количество фото для показа и запускает следующую функцию-шаг
        :param message: блок данных по последнему входящему сообщению пользователя
        """
        if message.text.lower() == 'да':
            new_message = 'Сколько фото показать (не больше 5)'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_answer_with_photos, repeat_step=False)
        elif message.text.lower() == 'нет':
            new_message = 'Ожидайте! Я работаю!'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message)
            try:
                current_hotels_list = utils.creat_hotel_list(data, command='highprice')
                hotel_list_for_history = list()
                for hotel in current_hotels_list:
                    hotel_list_for_history.append(f"\n{hotel.get('name')} - https://www.hotels.com/ho{hotel.get('id')}")
                    new_message = utils.result_by_hotel(hotel)
                    utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message)
            except Exception as e:
                new_message = 'Извините! По вашим параметрам мне не удалось собрать информацию!' \
                              '\nПопробуйте изменить параметры поиска!\n(Список команд: /help)'
                utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message)
                logging.exception(e)
            else:
                hotels_for_history = ', '.join(hotel_list_for_history)
                database.add_value(id_user=message.from_user.id, command='/highprice', date=data.time_command,
                                   city=data.city_name, value=hotels_for_history)
                new_message = 'Я завершил. Изучайте!\nДля вывода списка команд введите /help'
                utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message)
        else:
            new_message = 'Я ожидаю ответ: Да/Нет'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_number_photo, repeat_step=True)

    def get_answer_with_photos(message):
        """
        Функция второго порядка. Завершает запрос о количестве фото для показа
        и завершает выполнение команды /highprice выводом ее результата
        :param message: блок данных по последнему входящему сообщению пользователя
        """
        try:
            if int(message.text) > 5 or int(message.text) <=0:
                if int(message.text) > 5:
                    new_message = 'Я же просил не больше 5! Попробуем еще раз!\nСколько фото показать?'
                elif int(message.text) <= 0:
                    new_message = 'Меньше ноля и ноль тоже не подходит! Попробуем еще раз!\nСколько фото показать?'
                utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_answer_with_photos, repeat_step=True)
                return
        except Exception as e:
            new_message = 'Введите цифру!'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, next_func=get_answer_with_photos, repeat_step=True)
        else:
            new_message = 'Ожидайте! Я работаю!'
            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message)
            try:
                current_hotels_list = utils.creat_hotel_list(data, command='highprice')
                hotel_list_for_history = list()
                for hotel in current_hotels_list:
                    hotel_list_for_history.append(f"\n{hotel.get('name')} - https://www.hotels.com/ho{hotel.get('id')}")
                    new_message = utils.result_by_hotel(hotel)
                    utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message)
                    querystring = {"id": hotel.get('id')}
                    response = requests.request("GET", os.getenv('url_photos'), headers=json.loads(os.getenv('headers')), params=querystring)
                    response_dict = json.loads(response.text)
                    try:
                        hotel_photo_list = [elem.get('baseUrl') for elem in response_dict.get('hotelImages')]
                        for num in range(int(message.text)):
                            new_message = hotel_photo_list[num].partition('_{size}')[0] + '_z.jpg?impolicy=fcrop&w=500&h=280&q=high'
                            utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message, photo_transfer=True)
                    except Exception as e:
                        new_message = 'Извините! Фото этого отеля не нашел!'
                        utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message)
                        logging.exception(e)
            except Exception as e:
                new_message = 'Извините! По вашим параметрам мне не удалось собрать информацию!' \
                              '\nПопробуйте изменить параметры поиска!\n(Список команд: /help)'
                utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message)
                logging.exception(e)
            else:
                hotels_for_history = ', '.join(hotel_list_for_history)
                database.add_value(id_user=message.from_user.id, command='/highprice', date=data.time_command,
                                   city=data.city_name, value=hotels_for_history)
                new_message = 'Я завершил. Изучайте!\nДля вывода списка команд введите /help'
                utils.next_action_func(chat_bot=bot, user_message=message, bot_message=new_message)
    return get_city
