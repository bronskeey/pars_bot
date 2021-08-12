# coding: utf-8
import inspect

from bs4 import BeautifulSoup
from random import uniform, randint
from datetime import date
import requests
import os.path
import time
import ast
from tqdm import tqdm

# TODO: do something with functions inside of a function

class pars_rcoi(object):
	def __init__(self, url_):
		self.url = url_
		self.MAIN_NAME = url_.split('/')[-2]
		self.MAIN_TYPE = url_.split('/')[-3][:4]
		self.docs_list = []
		self.docs_links = []
		self.docs_og_names = []
		self.docs_last_m = dict()
		self.BAD_EXTENSIONS = ['wav','mp3', 'ru']
		self.bot_status = ''
		self.soup_div   = None
		self.last_dir = ''


	def get_info(self):
		"""
		- looking for 'p' and 'li' bc of 'gia-11' page which uses 'li'
		- there's a better way to do 'raw_link' analysis
		- 'requests.get(link_full_url)' works very slow for music files on a 'gia-9' page
		   so I won't check 'last-modified' for 'BAD_EXTENSIONS' files
		   bc RCOI won't modify music files
		- maybe '/n' replacing is not needed at the end
		- redo some things on small pages, maybe change link analysis
		"""

		print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [IN]  {inspect.stack()[0][3]}')
		response      = requests.get(self.url)
		soup          = BeautifulSoup(response.text, 'lxml')
		self.soup_div = soup.find('div', class_ = 'typicaltext')
		div_ps        = self.soup_div.find_all('p')
		div_uls       = self.soup_div.find_all('li')
		for raw_link in tqdm(div_ps+div_uls):
			link_A           = raw_link.find_all('a')
			doc_name         = raw_link.text.strip()
			link_descendants = [desc.name for desc in raw_link.descendants if desc.name is not None]
			if (len(link_A) == 1               and
				'a' in link_descendants        and
				doc_name not in self.docs_list and
				"dwnico" in str(link_A)):

				link_href      = link_A[0].get('href')
				link_full_url  = 'http://rcoi.mcko.ru' + link_href
				link_file_name = link_href.split('/')[-1].strip()
				link_file_ext  = link_file_name.split('.')[-1]
				if link_file_ext not in self.BAD_EXTENSIONS:
					full_link_response = requests.get(link_full_url)
					link_last_modified = full_link_response.headers.get('Last-Modified', False)
				else:
					link_last_modified = 0
				self.docs_list.append(doc_name)
				self.docs_links.append(link_full_url.strip())
				self.docs_og_names.append(link_file_name)
				self.docs_last_m[link_file_name] = link_last_modified
		self.docs_list = [doc.replace('\n','') for doc in self.docs_list]
		print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [OUT] {inspect.stack()[0][3]}')

		self.new_files()
		self.changed_files()


	def new_files(self):
		"""
		 - maybe it should be a class
		"""
		def main(self):
			diff_indexes = check_new_files(self)
			if diff_indexes:
				self.download_files(diff_indexes)
				dump_file_list(self)

		def check_new_files(self):
			"""
			- checking if there's new files on a page

			-returns: list of indexes
			"""
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [IN] {inspect.stack()[0][3]}')
			prev_file_list = get_previous_file_list(self)
			diff           = [x for x in self.docs_list if x not in prev_file_list]
			indexes        = [self.docs_list.index(d) for d in diff]
			if diff:
				print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [OUT] Found new files!')
			else:
				print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [OUT] No new files!')
			return indexes

		def get_previous_file_list(self):
			"""
			- looking for a file in ./file_lists/ directory
			   with file list in it

			-returns: file list
			"""
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [IN] {inspect.stack()[0][3]}')
			PATH      = f'./file_lists/{self.MAIN_TYPE}_{self.MAIN_NAME}.txt'
			if not os.path.exists(PATH):
				print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [INFO] Documents list not found!')
				print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [INFO] Creating a documents list..')
				dump_file_list(self)
			txt_file  = open(PATH, 'r', encoding="utf-8")
			file_list = [x.strip() for x in txt_file.readlines()]
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [OUT] File list found!')
			txt_file.close()
			return file_list

		def dump_file_list(self):
			"""
			- creating data file in ./file_lists/ directory
			"""
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [IN] {inspect.stack()[0][3]}')
			with open(f'./file_lists/{self.MAIN_TYPE}_{self.MAIN_NAME}.txt', "w", encoding="utf-8") as txt_file:
				for i,line in enumerate(self.docs_list):
					txt_file.write(line+'\n')
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [OUT] File list dumped')
		print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [IN] {inspect.stack()[0][3]}')
		# dump_file_list(self)
		main(self)
		print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [OUT] {inspect.stack()[0][3]}')

	def changed_files(self):
		"""
		 - maybe it should be a class
		"""
		def main(self):
			diff_indexes = check_modified_files(self)
			if diff_indexes:
				self.download_files(diff_indexes)
				dump_LM_list(self)

		def check_modified_files(self):
			"""
			- checking if there's a file on a web page before
			   comparing last modified data by comparing dicts
			- checking the diff. of last modified data

			- returns: list of indexes
			"""
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [IN] {inspect.stack()[0][3]}')
			prev_dict           = get_prev_modified_files(self)
			current_dict        = self.docs_last_m
			prev_dict 			= {name:date for name,date in prev_dict.items() if name in current_dict}
			difference          = prev_dict.items() ^ current_dict.items()
			names               = set([name for name,date in difference])
			indexes             = [self.docs_og_names.index(name) for name in names]
			if difference:
				print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [OUT] Found modified files!')
			else:
				print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [OUT] No modified files found!')
			return indexes

		def get_prev_modified_files(self):
			"""
			- looking for a file in ./file_lists/ directory
			   with last modified data in it

			-returns: dictionary with last modified data
			"""
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [IN] {inspect.stack()[0][3]}')
			PATH = f'./file_lists/{self.MAIN_TYPE}_{self.MAIN_NAME}_LM.txt'
			if not os.path.exists(PATH):
				print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [INFO] "Last modified" data not found!')
				print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [INFO] Creating a "last modified" data..')
				dump_LM_list(self)
			with open(PATH, "r") as text_file:
				data = ast.literal_eval(text_file.read())
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [OUT] "Last modified" data found!')
			return data	

		def dump_LM_list(self):
			"""
			- creating data file in ./file_lists/ directory
			"""
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [IN] {inspect.stack()[0][3]}')
			with open(f'./file_lists/{self.MAIN_TYPE}_{self.MAIN_NAME}_LM.txt', "w") as txt_file:
				data = str(self.docs_last_m)
				txt_file.write(data)
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [OUT] "Last modified" data created!"')
		print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [IN] {inspect.stack()[0][3]}')
		# dump_LM_list(self)
		main(self)
		print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [OUT] {inspect.stack()[0][3]}')

	def download_files(self,indexes):
		"""
		- apparently there's a quotes-related problem with file name
		  so I replace them with ''
		"""
		print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [IN] {inspect.stack()[0][3]}')
		download_date = date.today()
		self.last_dir = f'{download_date}_files'
		if not os.path.exists(self.last_dir):
			os.mkdir(self.last_dir)
		for i in indexes:
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [INFO] Downloading file #{i+1}')
			time_wait = uniform(1,4)
			time.sleep(time_wait)
			response = requests.get(self.docs_links[i])
			seed = str(randint(1, 1000))
			file_mask = f'{seed}_{self.MAIN_NAME}_{self.MAIN_TYPE}_'
			file_name_full = file_mask+self.docs_list[i][:180].replace(' ', '_').replace('"','')
			file_name_short = file_mask+self.docs_og_names[i].replace(' ', '_').replace('"','')
			new_file = open(f'./{self.last_dir}/{file_name_short}', 'wb')
			new_file.write(response.content)
			new_file.close()
			bot_status_text = f'[{self.MAIN_NAME}][{self.MAIN_TYPE}]File {file_name_full} downloaded!\n' + \
				'='*25
			self.bot_status += bot_status_text
			print(f'[{self.MAIN_NAME}] [{self.MAIN_TYPE}] [LOG] [INFO] File #{i+1} downloaded!')

if __name__ == '__main__':
	urls_organizers = ['http://rcoi.mcko.ru/organizers/info/gia-11/', 'http://rcoi.mcko.ru/organizers/info/gia-9/']
	urls_methodolog = ['http://rcoi.mcko.ru/organizers/methodological-materials/ege/', 'http://rcoi.mcko.ru/organizers/methodological-materials/gia-9/']
	urls = urls_organizers + urls_methodolog
	for url in urls:
		t = pars_rcoi(url)
		t.get_info()
		print(len(t.docs_list))
