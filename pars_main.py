# coding: utf-8
from random import uniform, randint
from log.logging_module import *
from bs4 import BeautifulSoup
from datetime import date
import requests
import os.path
import time
import ast
from tqdm import tqdm # для дебаггинга, можно выключить

pars_logger = Module_Logger(logging.getLogger(__name__))

# TODO: добавить весь раздел "Организаторам"
urls_organizers = ['http://rcoi.mcko.ru/organizers/info/gia-11/', 'http://rcoi.mcko.ru/organizers/info/gia-9/'] #
urls_methodolog = ['http://rcoi.mcko.ru/organizers/methodological-materials/ege/', 'http://rcoi.mcko.ru/organizers/methodological-materials/gia-9/']
urls = urls_organizers + urls_methodolog

class Pars_Get_Info(object):
    def __init__(self, url_):
        """
        Создаёт объект супа.
        Ищет теги <p> и <li> по страницам, последний из-за страницы с ЕГЭ.
        Запускает метод .get_info() для скрепинга данных.
        """
        self.docs_list = []
        self.docs_links = []
        self.docs_og_names = []
        self.docs_last_m = dict()
        self.BAD_EXTENSIONS = ['wav','mp3', 'ru']
        self.bot_status = ''
        self.last_dir = ''

        response = requests.get(url_)
        soup = BeautifulSoup(response.text, 'lxml')
        self.divs = soup.find('div', class_='typicaltext').find_all(['p','li'])

        section = soup.find('h1', class_='pagetitle').text
        grade = soup.find('li', class_='selected active').find('a').text
        self.info = {'section':section, 'grade':grade}
        pars_logger.logger.info(f'{self.info["section"]}-{self.info["grade"]} - Инициализация.')
        self.get_info()

    def get_info(self):
        """
        Анализирует все объекты на "подходящесть", заполняет все данные по файлам.
        Часть кода с 'requests.get(link_full_url)' работает очень медленно для музыкальных файлов
            инструкций, поэтому созданы 'BAD_EXTENSIONS'. Для них не проверяем дату изменения.
            Музыкальные файлы вряд ли будут изменять.
        """
        pars_logger.logger.info(f'{self.info["section"]}-{self.info["grade"]} - Собираем данные.')
        for raw_link in tqdm(self.divs): # tqdm используется для дебаггинга
            if self.link_checker(raw_link):
                link_href      = raw_link.find_all('a')[0].get('href')
                link_full_url  = 'http://rcoi.mcko.ru' + link_href
                link_file_name = link_href.split('/')[-1].strip()
                link_file_ext  = link_file_name.split('.')[-1]
                if link_file_ext not in self.BAD_EXTENSIONS:
                    full_link_response = requests.get(link_full_url)
                    link_last_modified = full_link_response.headers.get('Last-Modified', False)
                else:
                    link_last_modified = 0
                self.docs_list.    append(raw_link.text.strip().replace('\n',''))
                self.docs_links.   append(link_full_url.strip())
                self.docs_og_names.append(link_file_name)
                self.docs_last_m[link_file_name] = link_last_modified

    def link_checker(self, raw_link):
        """
        Проверяет каждый объект: есть ли иконка скачивания, есть ли один <a> для ссылки на файл.
        Часть с 'doc_name not in self.docs_list' тут из-за некоторых файлов, которые на странице
            больше одного раза в каком-нибудь закоменченом блоке.
        """
        link_A           = raw_link.find_all('a')
        doc_name         = raw_link.text.strip()
        link_descendants = [desc.name for desc in raw_link.descendants if desc.name is not None]
        if (len(link_A) == 1) and ('a' in link_descendants) and (doc_name not in self.docs_list) and ("dwnico" in str(link_A)):
            return True
        return False


class Pars_New_Files(object):
    def __init__(self, obj):
        self.docs_list = obj.docs_list
        self.docs_links = obj.docs_links
        self.docs_og_names = obj.docs_og_names
        self.indexes = None
        self.prev_file_list = None
        self.data = obj.info
        self.bot_status = obj.bot_status
        self.diff_type = 'Новые:'
        pars_logger.logger.debug(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - Инициализация ')

    def get_previous_file_list(self):
        """
        Ищет файл в папке ./file_lists/ с списком файлов.
        Если не находит, сохраняет текущий список файлов в такой файл.
        """

        pars_logger.logger.info(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - Ищем список файлов ')
        PATH = f'./file_lists/{self.data["section"]}_{self.data["grade"]}.txt'
        if not os.path.exists(PATH):
            pars_logger.logger.info(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - Список файлов не найден!')
            pars_logger.logger.info(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - Создаю список файлов')
            self.dump_file_list()
            self.prev_file_list = None
        else:
            with open(PATH, 'r', encoding="utf-8") as txt_file:
                self.prev_file_list = [x.strip() for x in txt_file.readlines()]
            pars_logger.logger.info(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - Список файлов найден!')

    def check_difference(self):
        """
        Сверяет список файлов с сайта с данными, сохраненными локально.
        Обновляет self.indexes номерами новых файлов.
        """
        new_files = [x for x in self.docs_list if x not in self.prev_file_list]
        self.indexes = [self.docs_list.index(d) for d in new_files]
        if new_files:
            pars_logger.logger.info(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - На странице найдены новые файлы!')
        else:
            pars_logger.logger.info(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - На странице не найдено новых файлов!')

    def dump_file_list(self):
        """
        Создаёт текстовый файл с списком файлов со страницы.
        """
        with open(f'./file_lists/{self.data["section"]}_{self.data["grade"]}.txt', "w", encoding="utf-8") as txt_file:
            for i,line in enumerate(self.docs_list):
                txt_file.write(line+'\n')
        pars_logger.logger.info(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - Список файлов сохранен.')


class Pars_Changed_Files(object):
    def __init__(self, obj):
        self.docs_list = obj.docs_list
        self.docs_links = obj.docs_links
        self.docs_og_names = obj.docs_og_names
        self.indexes = None
        self.prev_file_list = None
        self.data = obj.info
        self.bot_status = obj.bot_status
        self.docs_last_m = obj.docs_last_m
        self.diff_type = 'Изменены:'
        pars_logger.logger.debug(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - Инициализация ')


    def get_previous_file_list(self):
        """
        Ищет файл в папке ./file_lists/ с данными дат изменения файлов.
        Если не находит, сохраняет текущие данные с сайта в такой файл.
        """
        pars_logger.logger.info(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - Ищем даты изменения файлов')
        PATH = f'./file_lists/{self.data["section"]}_{self.data["grade"]}_LM.txt'
        if not os.path.exists(PATH):
            pars_logger.logger.info(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - Данные не найдены!')
            pars_logger.logger.info(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - Создаю файл с данными дат изменения файлов')
            self.dump_file_list()
            self.prev_file_list = None
        else:
            with open(PATH, "r") as text_file:
                self.prev_file_list = ast.literal_eval(text_file.read())
            pars_logger.logger.info(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - Данные найдены!')

    def check_difference(self):
        """
        Сверяет данные "дата изменения" файлов с сайта с данными, сохраненными локально.
        Предварительно проверяет, есть ли файл из локального списка на сайте.
        Обновляет self.indexes номерами изменённых файлов.
        """
        current_dict = self.docs_last_m
        prev_dict = {name: date_ for name, date_ in self.prev_file_list.items() if name in current_dict}
        fresh_modified_files = prev_dict.items() ^ current_dict.items()
        fresh_modified_files_names = set([name for name, date_ in fresh_modified_files])
        self.indexes = [self.docs_og_names.index(name) for name in fresh_modified_files_names]
        if fresh_modified_files:
            pars_logger.logger.info(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - На сайте найдены изменённые файлы!')
        else:
            pars_logger.logger.info(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - Изменённых файлов на сайте не найдено!')

    def dump_file_list(self):
        """
        Создаёт текстовый файл с данным по дате изменения каждого из файлов со страницы.
        """
        with open(f'./file_lists/{self.data["section"]}_{self.data["grade"]}_LM.txt', "w") as txt_file:
            txt_file.write(str(self.docs_last_m))
        pars_logger.logger.info(f'{self.data["section"]}-{self.data["grade"]}-{self.diff_type[:-1]} - Данные об изменении файлов сохранены.')


class Downloader(object):
    """
    Создает папку, скачивает туда все файлы по индексам.
    Между скачиваниями есть ожидания.
    Обновляет текст для бота.
    """
    def __init__(self, obj):
        pars_logger.logger.debug(f'{obj.data["section"]}-{obj.data["grade"]}-{obj.diff_type[:-1]} - Инициализация ')
        download_date = date.today()
        self.last_dir = f'./files/{download_date}_{obj.data["section"][:4]}_{obj.data["grade"]}_{obj.diff_type[:3].lower()}'
        self.indexes = obj.indexes
        self.docs_list = obj.docs_list
        self.docs_links = obj.docs_links
        self.docs_og_names = obj.docs_og_names

        if not os.path.exists(self.last_dir):
            os.mkdir(self.last_dir)

        self.bot_status = f'\n\n{obj.data["section"]}, {obj.data["grade"]}\n\n{obj.diff_type}\n\n'
        for i in self.indexes:
            pars_logger.logger.info(f'{obj.data["section"]}-{obj.data["grade"]}-{obj.diff_type[:-1]} - Скачиваем файл #{i + 1}')
            seed = randint(1, 1000)
            file_mask = f'{obj.data["grade"]}_{obj.data["section"]}_{seed}_'
            time_wait = uniform(1, 4)
            time.sleep(time_wait)
            file_name_short = file_mask + self.docs_og_names[i].replace(' ', '_').replace('"', '')
            with open(f'{self.last_dir}/{file_name_short}', 'wb') as new_file:
                response = requests.get(self.docs_links[i])
                new_file.write(response.content)
            self.bot_status += f'{i+1}. {self.docs_list[i]} - {self.docs_og_names[i]}\n'
            pars_logger.logger.info(f'{obj.data["section"]}-{obj.data["grade"]}-{obj.diff_type[:-1]} - Файл #{i + 1} скачен!')


def start_pars():
    """
    Это плохо, но пока так.
    Запускаем процесс, собираем данные для бота.

    :return: Список с сообщениями
    """
    message_data = list()
    for url in urls:
        main_obj = Pars_Get_Info(url)
        for obj in [Pars_New_Files(main_obj),Pars_Changed_Files(main_obj)]:
            obj.get_previous_file_list()
            if obj.prev_file_list: obj.check_difference()
            if obj.indexes:
                get_files = Downloader(obj)
                obj.dump_file_list()
                bot_status = get_files.bot_status
                get_files.bot_status = ''
                message_data.append([bot_status, get_files.last_dir])
            elif obj.bot_status == '':
                empty_text = f'{obj.data["section"]}, {obj.data["grade"]}\n' + \
                             f'{obj.diff_type}' + \
                             '\nНет обновлений!\n\n'
                message_data.append([empty_text,])
    return message_data
