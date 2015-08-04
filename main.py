from Savefile import Savefile
from sys import argv
from os import path

if __name__ == '__main__':
	if len(argv) > 1:
		savefiles = [Savefile(open(argv[i], 'rb')) for i in range(1, len(argv)) if path.isfile(argv[i])]
		print(savefiles)

	
