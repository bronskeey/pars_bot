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

#@pypeer_bot
token  = '1415917747:AAEgXuF8mmYGFUBaVbou0_eVQwzBvFnrFQM'
bot    = telebot.TeleBot(token)
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG) 
my_id  = '107579649'
users_random = {'65535': '2021-05-05'}
urls = ['http://rcoi.mcko.ru/organizers/info/gia-11/','http://rcoi.mcko.ru/organizers/info/gia-9/']


button_random_text = f'Random number'
button_scrap_text  = f'Get scrap info'
button_back_text   = f'Back to main menu'

    


@bot.message_handler(commands=['start'])
def start_f(message):
    """
    start
    """
    welcome(message.from_user.id, 0, False)


def welcome(id_c, id_m, edit_flag):
    start_string =\
        f"/start - Show main menu\n"+\
        f"/help  - Some info about\n"+\
        f"/random - Get a random number"
    
    start_markup    = types.InlineKeyboardMarkup(row_width=2)
    button_big      = types.InlineKeyboardButton(text='Show me big keys', callback_data='start_button_big')
    button_feedback = types.InlineKeyboardButton(text='Feedback', callback_data='start_button_feedback')
    button_secret   = types.InlineKeyboardButton(text='Secret', callback_data='start_button_secret')
    
    start_markup.add(
        button_big, 
        button_feedback,  
        button_secret)  
    
    if edit_flag:
        bot.edit_message_text(chat_id=id_c, message_id=id_m, text=start_string, reply_markup=start_markup)
    else:
        bot.send_message(id_c,                  
                     text = start_string,        
                     reply_markup = start_markup)
      
    
@bot.message_handler(commands=['help'])
def help_f(message):
    text = 'help'
    bot.reply_to(message,
                 text)


@bot.message_handler(commands=['random'])
def random_f(message):
    random_text = get_random()
    bot.send_message(message.chat.id,text = random_text)


@bot.message_handler(content_types=['text'])
def text_f(message):
    """
    plain text handler, 'привет' is the only option
    """
    if message.chat.type == 'private':

        if message.text == 'привет':
            bot.send_message(message.from_user.id,
                             'И тебе привет!')

        elif message.text == button_random_text:
            random_text = get_random()
            bot.send_message(message.chat.id,text = random_text)
    
        elif message.text == button_scrap_text:
            try:
                start_pars(message)
            except Exception as e:
                print(e)
            # for url in urls:
            #     pars_object = pars_rcoi(url)
            #     pars_object.get_info()
            #     status = pars_object.bot_status
            #     bot.send_message(message.chat.id,text = status)

        elif message.text == button_back_text:
            hide_big_markup      = types.ReplyKeyboardRemove(selective=True)
            big_buttons_off_text = f'--Buttons off--'
            bot.send_message(message.chat.id, 
                             big_buttons_off_text, 
                             reply_markup = hide_big_markup)
            welcome(message.chat.id,0,False)

def test_function(message):
    empty_text = '*' * 25 + \
     '\nNo new updates!\n' + \
     '*' * 25
    t = None
    status = empty_text if t == '' else 7
    bot.send_message(message.chat.id,text = status)
    threading.Timer(10, test_function, args=[message,]).start()

def start_pars(message):
    empty_text = '*' * 25 + \
                 '\nNo new updates!\n' + \
                 '*' * 25

    for url in urls:
        pars_object = pars_rcoi(url)
        pars_object.get_info()
        status = empty_text if pars_object.bot_status == '' else pars_object.bot_status
        bot.send_message(message.chat.id,text = status)

    threading.Timer(24*60*60, start_pars, args=[message,]).start()
        
def get_random():
    random_integer     = random.randint(0, 100)
    string =  f'Random number: {random_integer}'  
    return string
            

@bot.callback_query_handler(func=lambda call: call.data.startswith('start_button'))
def call_start_buttons(call):
    if call.data   == "start_button_big": 
        big_markup    = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)# на сколько наполнять ряд
        button_first  = types.KeyboardButton(button_random_text)
        button_second = types.KeyboardButton(button_scrap_text)
        button_back   = types.KeyboardButton(button_back_text)
        
        big_markup.add(
            button_first,
            button_second,
            button_back)
        
        big_buttons_on_text = f'--Buttons on--'
        
        bot.send_message(call.message.chat.id,
                         text = big_buttons_on_text,
                         reply_markup = big_markup)
        
    elif call.data == "start_button_feedback":
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


