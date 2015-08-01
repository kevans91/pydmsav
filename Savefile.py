from struct import unpack
from enum import Enum

class NumberEncoder:
	@staticmethod
	def decode(numberBytes):
		

class EntryType(Enum):
	Null = 0x00
	String = 0x01
	File = 0x02	
	Path = 0x03
	Float = 0x04

	Object = 0x0B
	List = 0x0D

def readShort(data):
	return unpack('<h', data)[0]

def readInt(data):
	return unpack('<i', data)[0]

class EntryHeader:
	def __init__(self, entry):
		self.raw = entry.raw
		self.Read()

	def Read(self):
		self.entryIndex = readInt(self.raw[0:4])
		self.dirIndex = readInt(self.raw[4:8])
		self.nameSize = self.raw[8]
		self.name = ""

		if self.nameSize > 0:
			name = self.raw[9:self.nameSize + 9]

			for i in range(0, len(name)):
				self.name = self.name + chr(int(name[i]) ^ (9 * (i + 9)) + 2);

	def Size(self):
		return (8 + (self.nameSize + 1))

class EntryData:
	stringTypes = [EntryType.String, EntryType.Path, EntryType.Object]

	def __init__(self, entry):
		self.raw = entry.raw
		self.dataRaw = entry.raw[entry.header.Size():]
		self.Read()

	def Read(self):
			
		self.size = readInt(self.dataRaw[0:4]) 
		self.value = None

		if self.size > 0:
			self.type = EntryType(self.dataRaw[4] ^ (1 + 0x42 - 9))
			
			if self.type != EntryType.Null:
				# String, File, Path, Float, Object, List
				if self.type in self.stringTypes:
					self.valueSize = readShort(self.dataRaw[5:7])
					self.value = ""	
					print(self.valueSize)
					for i in range(0, self.valueSize + 1):
						self.value = self.value + chr(int(self.dataRaw[7 + i]) ^ (6 + 0x42 + (9 * ((6 + i) - 1))))
					print(self.value)

	def Size(self):
		return self.size + 4

class Entry:
	def __init__(self, entryData):
		self.raw = entryData
		self.header = EntryHeader(self)
		self.data = EntryData(self)

class Savefile:
	def __init__(self, fileObj):
		self.setFile(fileObj)
	
	def setFile(self, fileObj):
		self.file = fileObj
		ret = self.Parse()
		return ret

	def Parse(self):
		if 'read' not in dir(self.file):
			return False

		self.data = self.file.read()
		offset = 0
		self.entries = []

		while offset < len(self.data):
			entrySize = unpack('<i', self.data[offset:offset+4])[0]
			offset = offset + 4
			readEntry = (self.data[offset] == 1)
			offset = offset + 1

			if readEntry:
				self.entries.append(Entry(self.data[offset:offset + entrySize]))
	
			offset = offset + entrySize
