# coding: utf-8
# @school_updater_bot
import schedule as schedule
from threading import Thread
from time import sleep
from config import my_token, my_id
from log.logging_module import *
from pars_main import start_pars
import telebot
import sys
bot_logger = Module_Logger(telebot.logger)
bot_logger.logger.setLevel(logging.DEBUG)
bot_logger.logger.handlers = [h for h in bot_logger.logger.handlers if isinstance(h, logging.FileHandler)]
token = my_token
bot = telebot.TeleBot(token)
work_chat_link = 't.me/rcoi_tale'

# TODO: написать тестер через списки файлов
# TODO: сделать конфиги для вольюма докера:
#   - айди рабочего чата, админа
#   - расписание


@bot.message_handler(commands=['help'])
def command_help(message):
    """
    Для администратора выдаёт стату и скрытые команды, для остальных текущую ситуацию в двух словах.
    """
    bot_logger.logger.debug('/help')
    if message.from_user.id == int(my_id):
        log_folder_size = sum([os.stat('./log/'+file).st_size for file in os.listdir('./log/')])
        log_folder_size_unit = 'КБ'
        log_folder = [log_folder_size / 1024, log_folder_size_unit]
        files_folder_size = sum(os.stat(os.path.join(dirpath,filename)).st_size for dirpath, dirnames, filenames in os.walk('./files/') for filename in filenames)
        files_folder_size_unit = 'КБ'
        files_folder = [files_folder_size / 1024, files_folder_size_unit]
        for volume in [log_folder, files_folder]:
            if volume[0] > 1024:
                volume[0] /= 1024
                volume[1] = 'МБ'
        help_string = 'Привет, вот лист комманд:\n/_start, /_stop, /_get, /_get_logs, /_clean_files\n' \
                      f'Сейчас:\n - размер логов {log_folder[0]:.2f} {log_folder[1]}\n - размер скачанных файлов {files_folder[0]:.2f} {files_folder[1]}'
    else:
        help_string = f'Привет, этот бот работает в канале {work_chat_link}, четыре раза в день проверяет неназванный сайт и рассказывает, что там новенького.' \
                      f'Расписание: 07:00, 10:00, 17:00, 23:00'
    bot.send_message(message.chat.id, text = help_string)


@bot.message_handler(commands=['_get_logs'])
def adm_command_get_logs(message):
    """
    Только для администратора: присылает два лог-файла
    """
    bot_logger.logger.debug('/_get_logs')
    if message.from_user.id == int(my_id):
        log_path = bot_logger.log_folder
        log_list = [file for file in os.listdir(log_path) if file.endswith(".txt")]
        try:
            for file in log_list:
                with open(log_path + file, 'rb') as f:
                    bot.send_document(message.chat.id, f)
        except Exception as e:
            frame = traceback.extract_tb(sys.exc_info()[2])
            line_no = str(frame[0]).split()[4]
            bot_logger.error_log(line_no)
            bot.send_message(my_id, text=f'У нас ошибка, не смогли отправить логи.\nОшибка: {e}')
    else:
        pass


@bot.message_handler(commands=['_clean_files'])
def adm_command_clean_files(message):
    """
    Только для администратора: удаляет скачанные файлы
    """
    import shutil
    bot_logger.logger.debug('/_clean_files')
    if message.from_user.id == int(my_id):
        try:
            files_path = './files/'
            shutil.rmtree(files_path)
            os.mkdir(files_path)
            bot.send_message(message.chat.id, text='Файлы удалены.')
        except OSError as e:
            bot_logger.logger.error(f"Error: {e.filename} - {e.strerror}.")
            bot.send_message(my_id, text=f'У нас ошибка, не смогли удалить файлы.\n{e.filename} - {e.strerror}')
        except Exception as e:
            frame = traceback.extract_tb(sys.exc_info()[2])
            line_no = str(frame[0]).split()[4]
            bot_logger.error_log(line_no)
            bot.send_message(my_id, text=f'У нас ошибка, не смогли удалить файлы.\n{e}')
    else:
        pass


@bot.message_handler(commands=['_stop'])
def command_stop(message):
    """
    Останавливает все задачи из расписания
    """
    bot_logger.logger.debug('/_stop')
    if message.from_user.id == int(my_id):
        schedule.clear()
        bot.send_message(message.chat.id, 'Задачи остановлены')
    else:
        pass


@bot.message_handler(commands=['_get'])
def command_stop(message):
    """
    Останавливает все задачи из расписания
    """
    bot_logger.logger.debug('/_get')
    if message.from_user.id == int(my_id):
        all_jobs = schedule.get_jobs()
        bot.send_message(message.chat.id, text=str(all_jobs))
    else:
        pass


@bot.message_handler(commands=['_start'])
def command_start(message):
    """
    Запускает расписание
    """
    bot_logger.logger.debug('/_start')
    if message.from_user.id == int(my_id):
        schedule.every().day.at("07:00").do(action, message)
        schedule.every().day.at("10:00").do(action, message)
        schedule.every().day.at("17:00").do(action, message)
        schedule.every().day.at("23:00").do(action, message)
        Thread(target=schedule_checker).start()
        bot.send_message(message.chat.id, 'Задачи запущены')
    else:
        pass


def action(msg):
    """
    Запускает общение с парсером. Получает от него список с сообщениями двух типов:
    1) из 2 элементов -- сообщение + файлы
    2) из 1 элемента -- нет обновлений
    TODO: собирать "нет обновлений" из всех разделов в одно сообщение, выводить последним
    """
    try:
        bot.send_message(msg.chat.id, text='Начинаем упражнение', disable_notification=True)
        bot_logger.logger.debug('Парсер начал работу')
        messages = start_pars()
    except Exception as e:
        frame = traceback.extract_tb(sys.exc_info()[2])
        line_no = str(frame[0]).split()[4]
        bot_logger.error_log(line_no)
        bot.send_message(msg.chat.id, text="Извините, что-то сломалось. Админу сообщили, скоро всё починим.")
        bot.send_message(my_id, text=f'У нас ошибка, парсер не запустился.\n{e}')
    else:
        for msg_data in messages:
            if len(msg_data) == 2:
                bot.send_message(msg.chat.id, text=msg_data[0])
                data_dir = f'{msg_data[1]}/'
                file_list = os.listdir(data_dir)
                for file in file_list:
                    try:
                        with open(data_dir + file, 'rb') as f:
                            bot.send_document(msg.chat.id, f)
                    except Exception as e:
                        frame = traceback.extract_tb(sys.exc_info()[2])
                        line_no = str(frame[0]).split()[4]
                        bot_logger.error_log(line_no)
                        bot.send_message(msg.chat.id, text="Извините, что-то сломалось, я не смог отправить вам файл. Админу сообщили, скоро всё починим.")
                        bot.send_message(my_id, text=f'У нас ошибка, не смогли отправить файл.\n{e}')
            elif len(msg_data) == 1:
                bot.send_message(msg.chat.id, text=msg_data[0], disable_notification=True)
        bot.send_message(msg.chat.id, text='Закончили упражнение', disable_notification=True)
        bot_logger.logger.debug('Парсер закончил работу')

def schedule_checker():
    # TODO: это не очень красиво, может заменить скедулер
    while True:
        schedule.run_pending()
        sleep(1)

bot.polling(none_stop=True)

