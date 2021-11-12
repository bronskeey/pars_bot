#coding: utf-8
import telebot
import logging
from telebot import types
import random
import os
import csv
from datetime import datetime
from pars_main import pars_rcoi
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
        bot.send_message(message.chat.id, text='='*5 + 'Parser started' + '='*5, disable_notification=True)
        start_pars(message)
        bot.send_message(message.chat.id, text='='*6 + 'Parser ended' + '='*6, disable_notification=True)
    else:
        bot.reply_to(message, text="Sorry, you don't have enough rigths to do this!")
        print(f'{message.from_user.id} tried to start the parser')


def start_pars(message):
    """
    Idk what is going on here

    """
    for url in urls:
        pars_object = pars_rcoi(url)
        pars_object.get_info()
        if pars_object.bot_status == '':
            empty_text = '*' * 25 + \
                         f'\n{pars_object.MAIN_TYPE}\n' + \
                         f'\n{pars_object.MAIN_NAME}\n' + \
                         '\nNo new updates!\n' + \
                         '*' * 25
            status = empty_text
            bot.send_message(message.chat.id, text=status, disable_notification=True)
        else:
            status    = pars_object.bot_status
            bot.send_message(message.chat.id, text=status)
            data_dir  = f'./{pars_object.last_dir}/'
            file_list = os.listdir(data_dir)
            for file in file_list:
                try:
                    with open(data_dir + file, 'rb') as f:
                        bot.send_document(message.chat.id, f)
                except PermissionError as e:
                    bot.send_message(message.chat.id, text="Something went wrong. I can't send you the files.")
                    print(e)
                    print(data_dir)
                    print(file_list)

    threading.Timer(P_HOUR * 60 * 60, start_pars, args=[message, ]).start()

# TODO: everything below this line is not needed


@bot.message_handler(commands=['random'])
def random_command(message):
    """
    TODO: delete this

     - getting random number from 'get_random' function,
       sending it back to chat.
    """
    random_text = get_random()
    bot.send_message(message.chat.id,text = random_text)

def get_random():
    random_integer     = random.randint(0, 100)
    string =  f'Random number: {random_integer}'
    return string


@bot.callback_query_handler(func=lambda call: call.data.startswith('start_button'))
def call_start_buttons(call):
    """
     - handling the only call for feedback button
     - calling 'save_csv' to save feedback messages to 'data/feedback.csv'
    """
    if call.data == "start_button_feedback":
        keyboard_markup = types.ForceReply(selective=False)
        msg             = bot.send_message(call.message.chat.id,
                                             'Оставьте свой отзыв! ',
                                             reply_markup = keyboard_markup)
        bot.register_next_step_handler(msg, save_csv)

def save_csv(message):
    file_exists  = os.path.isfile('data/feedback.csv')
    with open('data/feedback.csv', 'a', newline='') as csvfile:
        fieldnames = ['id', 
                  'name', 
                  'last_name', 
                  'username', 
                  'date', 
                  'time', 
                  'text']
        writer     = csv.DictWriter(csvfile, 
                                fieldnames=fieldnames, 
                                delimiter=';')
        if not file_exists:
            writer.writeheader() 
            
        now = datetime.now()
        row = {'id'       : f'{message.from_user.id:10}', 
           'name'     : f'{message.from_user.first_name}',
           'last_name': f'{message.from_user.last_name}', 
           'username' : f'{message.from_user.username}',
           'date'     : f'{now:%Y-%m-%d}', 
           'time'     : f'{now:%H:%M:%S}', 
           'text'     : f'{message.text:>10}'}
        writer.writerow(row)
        bot.send_message(my_id, f'New feedback!')
        bot.send_message(message.from_user.id, f'Thank you!')

bot.polling(none_stop=True)
