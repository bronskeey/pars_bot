# coding: utf-8
from bs4 import BeautifulSoup
from random import uniform, randint
import requests
import os.path
import time
import ast
'''
20.07: maybe it is working
	   changelog:
	   		- comparing dicts to check if there's a file before LM
	   		 


'''
class pars_rcoi(object):
	def __init__(self, url):
		self.url = url
		self.MAIN_NAME = url.split('/')[-2]
		self.docs_list = []
		self.docs_links = []
		self.docs_og_names = []
		self.docs_last_m = dict()
		self.BAD_EXTENSIONS = ['wav','mp3']
		self.bot_status = ''
		self.soup_div   = None


	def get_info(self):
		"""
		- looking for 'p' and 'li' bc of 'gia-11' page which uses 'li'
		- there's a better way to do 'raw_link' analysis
		- 'requests.get(link_full_url)' works very slow for music files on a 'gia-9' page
		   so I won't check 'last-modified' for 'BAD_EXTENSIONS' files
		   bc RCOI won't modify music files
		- maybe '/n' replacing is not needed at the end
		"""

		print(f'[{self.MAIN_NAME}][LOG][IN] Getting soup ready')
		response      = requests.get(self.url)
		soup          = BeautifulSoup(response.text, 'lxml')
		self.soup_div = soup.find('div', class_ = 'typicaltext')
		div_ps        = self.soup_div.find_all('p')
		div_uls       = self.soup_div.find_all('li')

		for raw_link in div_ps+div_uls:
			link_A           = raw_link.find_all('a')
			doc_name         = raw_link.text.strip()
			link_descendants = [desc.name for desc in raw_link.descendants if desc.name is not None]

			if (len(link_A) == 1 and 
			'a' in link_descendants and 
			doc_name not in self.docs_list):

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

		self.new_files()
		self.changed_files()

		# self.new_files()
		# self.changed_files()

	def new_files(self):
		def main(self):
			# dump_file_list(self)
			diff_indexes = check_new_files(self)
			if diff_indexes:
				self.download_files(diff_indexes)
				dump_file_list(self)

		def check_new_files(self):
			print(f'[{self.MAIN_NAME}][LOG][IN] Checking new files..')

			prev_file_list = get_previous_file_list(self)
			diff           = [x for x in self.docs_list if x not in prev_file_list]
			indexes        = [self.docs_list.index(d) for d in diff]

			if diff:
				print(f'[{self.MAIN_NAME}][LOG][OUT] Found new files!')
			else:
				print(f'[{self.MAIN_NAME}][LOG][OUT] No new files!')

			return indexes

		def get_previous_file_list(self):
			print(f'[{self.MAIN_NAME}][LOG][IN] Checking previous file list..')

			PATH      = 'file_lists/' + self.MAIN_NAME + '.txt'

			if not os.path.exists(PATH):
				print(f'[{self.MAIN_NAME}][LOG][INFO] Documents list not found!')
				print(f'[{self.MAIN_NAME}][LOG][INFO] Creating a documents list..')
				dump_file_list(self)

			txt_file  = open('file_lists/' + self.MAIN_NAME + '.txt', 'r', encoding="utf-8")
			file_list = [x.strip() for x in txt_file.readlines()]

			print(f'[{self.MAIN_NAME}][LOG][OUT] File list found!')
			txt_file.close()
			return file_list

		def dump_file_list(self):
			print(f'[{self.MAIN_NAME}][LOG][IN] Dumping file list')

			with open('file_lists/' + self.MAIN_NAME+'.txt', "w", encoding="utf-8") as txt_file:
				for i,line in enumerate(self.docs_list):
					txt_file.write(line+'\n')

			print(f'[{self.MAIN_NAME}][LOG][OUT] File list dumped')

		# dump_file_list(self)
		main(self)

	def changed_files(self):
		def main(self):		
			# dump_LM_list(self)
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
			print(f'[{self.MAIN_NAME}][LOG][IN] Checking modified files..')
			prev_dict = get_prev_modified_files(self)
			current_dict = self.docs_last_m

			prev_dict 			= {name:date for name,date in prev_dict.items() if name in current_dict}
			difference          = prev_dict.items() ^ current_dict.items()
			names               = set([name for name,date in difference])
			indexes             = [self.docs_og_names.index(name) for name in names]
			
			if difference:
				print(f'[{self.MAIN_NAME}][LOG][OUT] Found modified files!')
			else:
				print(f'[{self.MAIN_NAME}][LOG][OUT] No modified files found!')

			return indexes

		def get_prev_modified_files(self):
			"""
			 - maybe "else" needed after checking if there's file
			"""
			print(f'[{self.MAIN_NAME}][LOG][IN] Checking previous "last modified" data')

			# data = dict()
			PATH = 'file_lists/' + self.MAIN_NAME + '_LM' + '.txt'

			if not os.path.exists(PATH):
				print(f'[{self.MAIN_NAME}][LOG][INFO] "Last modified" data not found!')
				print(f'[{self.MAIN_NAME}][LOG][INFO] Creating a "last modified" data..')
				dump_LM_list(self)

			with open('file_lists/' + self.MAIN_NAME + '_LM' + '.txt', 'r') as text_file:
				data = ast.literal_eval(text_file.read())

			print(f'[{self.MAIN_NAME}][LOG][OUT] "Last modified" data found!')
			return data	

		def dump_LM_list(self):
			print(f'[{self.MAIN_NAME}][LOG][IN] Creating "last modified" data')

			with open('file_lists/' + self.MAIN_NAME + '_LM' + '.txt', "w") as txt_file:
				data = str(self.docs_last_m)
				txt_file.write(data)

			print(f'[{self.MAIN_NAME}][LOG][OUT] "Last modified" data created!"')

		# dump_LM_list(self)
		main(self)
	

	def download_files(self,indexes):
		"""
		- shortening to 45 characters is causing problems
		  bc of identical file names.
		- apparently there's a quotes-related problem with file name
		  so I replace them with ''
		"""
		print(f'[{self.MAIN_NAME}][LOG][IN] Downloading new files..')

		for i in indexes:
			print(f'[{self.MAIN_NAME}][LOG][INFO] Downloading file #{i+1}')

			seed = uniform(1,4)
			time.sleep(seed)
			response = requests.get(self.docs_links[i])

			file_ext        = self.docs_og_names[i].split('.')[-1]
			file_name_site_short  = str(self.docs_list[i][:45])
			file_name       = str(randint(1,500)) + f'_'
			file_name      += file_name_site_short + f'.' + file_ext
			file_name       = file_name.replace(' ', '_')		
			file_name 		= file_name.replace('"','')			

			new_file = open(f'files/{self.MAIN_NAME}_{file_name}', 'wb')
			new_file.write(response.content)
			new_file.close()
			
			self.bot_status += f'[{self.MAIN_NAME}]File {file_name} downloaded!\n'
			print(f'[{self.MAIN_NAME}][LOG][INFO] File #{i+1} downloaded!')


if __name__ == '__main__':
	urls = ['http://rcoi.mcko.ru/organizers/info/gia-11/', 'http://rcoi.mcko.ru/organizers/info/gia-9/']
	for url in urls:
		t = pars_rcoi(url)
		t.get_info()

