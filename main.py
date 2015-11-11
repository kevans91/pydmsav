from Savefile import Savefile
from sys import argv
from os import path
from json import dumps

if __name__ == '__main__':
	if len(argv) > 1:
		savefiles = [Savefile(open(argv[i], 'rb')) for i in range(1, len(argv)) if path.isfile(argv[i])]
		for i in savefiles:
			rep = i.__raw__()
			print(dumps(rep, indent=1))
