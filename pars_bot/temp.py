from pars_main import pars_rcoi
urls = ['http://rcoi.mcko.ru/organizers/info/gia-11/','http://rcoi.mcko.ru/organizers/info/gia-9/']


test = pars_rcoi(urls[0])
test.get_info()

print(test.bot_status)