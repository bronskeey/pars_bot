#coding: utf-8
import telebot
import logging
from telebot import types
# import random
import os
# import csv
# from datetime import datetime
from pars_main import Pars_Get_Info, Pars_Changed_Files, Pars_New_Files, Downloader
import threading

from config import my_pi, my_id


#@pypeer_bot
token = my_pi
bot    = telebot.TeleBot(token)
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
urls_organizers = ['http://rcoi.mcko.ru/organizers/info/gia-11/', 'http://rcoi.mcko.ru/organizers/info/gia-9/'] #
urls_methodolog = ['http://rcoi.mcko.ru/organizers/methodological-materials/ege/', 'http://rcoi.mcko.ru/organizers/methodological-materials/gia-9/']
urls = urls_organizers + urls_methodolog

# REPEAT PARSE EVERY 'P_HOUR' HOURS
P_HOUR = 24

# TODO: separate this thing into two files
# TODO: impement creating file lists w/o running the bot

@bot.message_handler(commands=['start'])
def start_command(message):
    """
    TODO: do not do that, implement basic start behaviour
    TODO: create list of commands in bot

     - calling 'welcome' function for the list of commands
    """
    welcome(message.chat.id)

def welcome(id_c):
    """
    TODO: put this in a help command

    """
    start_string =\
        f"/start - Show main menu\n"+\
        f"/pars  - Start RCOI parser\n"+\
        f"/random - Get a random number"
    start_markup    = types.InlineKeyboardMarkup(row_width=2)
    button_feedback = types.InlineKeyboardButton(text='Feedback', callback_data='start_button_feedback')
    start_markup.add(
        button_feedback)
    bot.send_message(id_c, text = start_string, reply_markup = start_markup)


@bot.message_handler(commands=['pars'])
def pars_command(message):
    if message.from_user.id == int(my_id):
        bot.send_message(message.chat.id, text='Начинаем упражнение', disable_notification=True)
        start_pars(message)
        bot.send_message(message.chat.id, text='Закончили упражнение', disable_notification=True)
    else:
        bot.reply_to(message, text="Изивините, похоже, у вас нет прав на выполнение этой команды.")
        print(f'{message.from_user.id} tried to start the parser')


def start_pars(message):
    status = ''
    for url in urls:

        main_obj = Pars_Get_Info(url)

        for obj in [Pars_New_Files(main_obj),Pars_Changed_Files(main_obj)]:
            obj.get_previous_file_list()
            obj.check_difference()
            if obj.indexes:
                get_new_files = Downloader(obj)
                obj.dump_file_list()
                bot_status = get_new_files.bot_status
                bot.send_message(message.chat.id, text=bot_status)
                data_dir = f'./{get_new_files.last_dir}/'
                file_list = os.listdir(data_dir)
                for file in file_list:
                    try:
                        with open(data_dir + file, 'rb') as f:
                            bot.send_document(message.chat.id, f)
                            get_new_files.bot_status = ''
                    except Exception as e:
                        bot.send_message(message.chat.id, text="Something went wrong. I can't send you the files.")
            elif obj.bot_status == '':
                empty_text = f'{obj.data["section"]}, {obj.data["grade"]}\n' + \
                             f'{obj.diff_type}' + \
                             '\nНет обновлений!\n\n' + \
                             '*' * 25
                status = empty_text
                bot.send_message(message.chat.id, text=status, disable_notification=True)


    threading.Timer(P_HOUR * 60 * 60, start_pars, args=[message, ]).start()

bot.polling(none_stop=True)
