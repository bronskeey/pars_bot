# coding: utf-8
from bs4 import BeautifulSoup
from random import uniform, randint
from datetime import date
import requests
import os.path
import time
import ast
from tqdm import tqdm

# TODO: redo dumper

class Pars_Get_Info(object):
	def __init__(self, url_):
		"""
		looking for 'p' and 'li' bc of 'gia-11' page which uses 'li'

		TODO: do this thing need MAIN_NAME and MAIN_TYPE at all?
		"""
		self.MAIN_NAME = url_.split('/')[-2]
		self.MAIN_TYPE = url_.split('/')[-3][:4]
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
		self.get_info()

	def get_info(self):
		"""
		- 'requests.get(link_full_url)' works very slow for music files on a 'gia-9' page
		   so I won't check 'last-modified' for 'BAD_EXTENSIONS' files
		   bc RCOI won't modify music files
		"""
		for raw_link in tqdm(self.divs):
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
		this thing checking if link is good for us to analyze it.
		page containg several bad links etc.
		"""
		link_A           = raw_link.find_all('a')
		doc_name         = raw_link.text.strip()
		link_descendants = [desc.name for desc in raw_link.descendants if desc.name is not None]
		if (len(link_A) == 1) and ('a' in link_descendants) and (doc_name not in self.docs_list) and ("dwnico" in str(link_A)):
			return True
		return False


class Pars_New_Files(object):
	def __init__(self, obj):
		self.MAIN_NAME = obj.MAIN_NAME
		self.MAIN_TYPE = obj.MAIN_TYPE
		self.docs_list = obj.docs_list
		self.docs_links = obj.docs_links
		self.docs_og_names = obj.docs_og_names
		self.indexes = None
		self.prev_file_list = None
		self.data = obj.info
		self.bot_status = obj.bot_status
		self.diff_type = 'Новые:'

	def get_previous_file_list(self):
		"""
		Looking for a list of files in ./file_lists/ directory
		Updating self.prev_file_list
		"""
		PATH = f'./file_lists/{self.MAIN_TYPE}_{self.MAIN_NAME}.txt'
		if not os.path.exists(PATH):
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] File list not found!')
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] Creating a file list..')
			self.dump_file_list()
			self.prev_file_list = None
		else:
			with open(PATH, 'r', encoding="utf-8") as txt_file:
				self.prev_file_list = [x.strip() for x in txt_file.readlines()]
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] File list found!')

	def check_difference(self):
		"""
		Checking if there's new files on a page
		Updating self.indexes
		"""
		new_files = [x for x in self.docs_list if x not in self.prev_file_list]
		self.indexes = [self.docs_list.index(d) for d in new_files]
		if new_files:
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] Found new files!')
		else:
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] No new files!')

	def dump_file_list(self):
		"""
		Creating a .txt data file in ./file_lists/ directory
		"""
		with open(f'./file_lists/{self.MAIN_TYPE}_{self.MAIN_NAME}.txt', "w", encoding="utf-8") as txt_file:
			for i,line in enumerate(self.docs_list):
				txt_file.write(line+'\n')
		print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] File list dumped')


class Pars_Changed_Files(object):
	def __init__(self, obj):
		self.MAIN_NAME = obj.MAIN_NAME
		self.MAIN_TYPE = obj.MAIN_TYPE
		self.docs_list = obj.docs_list
		self.docs_links = obj.docs_links
		self.docs_og_names = obj.docs_og_names
		self.indexes = None
		self.prev_file_list = None
		self.data = obj.info
		self.bot_status = obj.bot_status
		self.docs_last_m = obj.docs_last_m
		self.diff_type = 'Изменены:'


	def get_previous_file_list(self):
		"""
		Looking for a file in ./file_lists/ directory with last modified data in it.
		Updates dictionary with last modified data.
		"""
		PATH = f'./file_lists/{self.MAIN_TYPE}_{self.MAIN_NAME}_LM.txt'
		if not os.path.exists(PATH):
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] "Last modified" data not found!')
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] Creating "last modified" data..')
			self.dump_file_list()
			self.prev_file_list = None
		else:
			with open(PATH, "r") as text_file:
				self.prev_file_list = ast.literal_eval(text_file.read())
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] "Last modified" data found!')

	def check_difference(self):
		"""
		- checking if there's a file on a web page before
		   comparing last modified data by comparing dicts
		- checking the diff. of last modified data
		"""
		current_dict = self.docs_last_m
		prev_dict = {name: date_ for name, date_ in self.prev_file_list.items() if name in current_dict}
		fresh_modified_files = prev_dict.items() ^ current_dict.items()
		fresh_modified_files_names = set([name for name, date_ in fresh_modified_files])
		self.indexes = [self.docs_og_names.index(name) for name in fresh_modified_files_names]
		if fresh_modified_files:
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] Found modified files!')
		else:
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] No modified files found!')

	def dump_file_list(self):
		"""
		- creating data file in ./file_lists/ directory
		"""
		with open(f'./file_lists/{self.MAIN_TYPE}_{self.MAIN_NAME}_LM.txt', "w") as txt_file:
			txt_file.write(str(self.docs_last_m))
		print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] "Last modified" data updated!"')


class Downloader(object):
	def __init__(self, obj):
		download_date = date.today()
		self.last_dir = f'{download_date}_{obj.data["section"][:4]}_{obj.data["grade"]}_{obj.diff_type[:3].lower()}'
		self.indexes = obj.indexes
		self.MAIN_NAME	 = obj.MAIN_NAME
		self.MAIN_TYPE = obj.MAIN_TYPE
		self.docs_list = obj.docs_list
		self.docs_links = obj.docs_links
		self.docs_og_names = obj.docs_og_names

		if not os.path.exists(self.last_dir):
			os.mkdir(self.last_dir)

		self.bot_status = f'\n\n{obj.data["section"]}, {obj.data["grade"]}\n\n{obj.diff_type}\n\n'
		for i in self.indexes:
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] Downloading file #{i + 1}')
			seed = randint(1, 1000)
			file_mask = f'{self.MAIN_NAME}_{self.MAIN_TYPE}_{seed}_'
			time_wait = uniform(1, 4)
			time.sleep(time_wait)
			file_name_short = file_mask + self.docs_og_names[i].replace(' ', '_').replace('"', '')
			with open(f'./{self.last_dir}/{file_name_short}', 'wb') as new_file:
				response = requests.get(self.docs_links[i])
				new_file.write(response.content)
			self.bot_status += f'{i+1}. {self.docs_list[i]} - {self.docs_og_names[i]}\n'
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] File #{i + 1} downloaded!')