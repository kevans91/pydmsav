from struct import unpack
from enum import Enum

class EntryType(Enum):
	Null = 0x00
	String = 0x01
	File = 0x02	
	Path = 0x03
	Float = 0x04

	Object = 0x0B
	List = 0x0D

class ListType(Enum):
	Plain = 0x00
	Associative = 0x01

class ParserContext:
	def __init__(self):
		self.offset = 0
		self.entryOffset = 0
		self.dataOffset = 0
		self.dataStart = 0

def readShort(data):
	return unpack('<h', data)[0]

def readInt(data):
	return unpack('<i', data)[0]

def readFloat(data):
	return unpack('<f', data)[0]

class FileEntry:
	def __init__(self, dataArray):
		self.blockHeader = dataArray[0:11]
		self.fileSize = readInt(self.blockHeader[0:4])
		self.crc32 = readInt(self.blockHeader[4:8])
		self.resourceType = self.blockHeader[8]
		self.nameLength = readShort(self.blockHeader[9:11])
		self.name = ""
		self.data = ""
		
		name = dataArray[11:(11 + self.nameLength)]
		for i in name:
			self.name = self.name + chr(i)

		data = dataArray[(-1 * self.fileSize):]
		for i in data:
			self.data = self.data + chr(i)

	def Size(self):
		return 11 + len(self.name) + len(self.data)

class EntryHeader:
	def __init__(self, entry, context):
		self.raw = entry.raw
		self.context = context
		self.Read()
		self.context.dataStart = self.Size() + 5

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

	def __init__(self, entry, context):
		self.entry = entry
		self.raw = entry.raw
		self.context = context
		self.listType = None
		self.dataRaw = entry.raw[entry.header.Size():]
		self.Read()

	def Read(self):
			
		self.size = readInt(self.dataRaw[0:4]) 
		self.value = None
		if self.size > 0:
			self.type = EntryType(self.dataRaw[4] ^ (0x40 - 6))
			self.context.dataOffset = self.context.dataStart + 5
	
			dataSlice = self.dataRaw[5:(5 + self.size) - 1]
			dataArray = []

			if self.type != EntryType.Null:
				# String, File, Path, Float, Object, List

				dataSize = len(dataSlice)
		
				for i in range(0, dataSize):
					dataArray.append((dataSlice[i] ^ (0x43 + (9 * i))) & 0xFF)

				self._ReadValue(self.type, bytearray(dataArray))

	def _ReadValue(self, type, dataArray):
		if type in self.stringTypes:
			self.valueSize = readShort(dataArray[0:2])
			self.value = dataArray[2:(2 + self.valueSize)].decode('utf-8')
			return self.valueSize + 2
		elif type == EntryType.Float:
			self.value = readFloat(dataArray[0:4])	
			return 4
		elif type == EntryType.File:
			self.value = FileEntry(dataArray)
			return self.value.Size()
		elif type == EntryType.List:
			seqCount = readInt(dataArray[0:4])
			listType = ListType(dataArray[4])

			if self.listType is None:
				self.listType = listType

			if listType == ListType.Plain:
				self.value = value = []
			else:
				self.value = value = {}

			assocMode = False
			listEnd = False

			idx = seqNum = 0
			dataArray = dataArray[5:]
			i = 0

			while i < len(dataArray) and seqNum < seqCount:
				seqNum = seqNum + 1
				dataType = EntryType(dataArray[i])
				i = i + 1
				sz = self._ReadValue(dataType, dataArray[i:])
				i = i + sz	

				if dataType == EntryType.Null and i == len(dataArray):
					break

				if listType == ListType.Associative:
					swapAssoc = False

					if seqNum == seqCount and not listEnd:
						seqCount = readInt(dataArray[i:i+4])
						listEnd = (dataArray[i + 4] == 0)
						i = i + 5
						seqNum = 0
						assocMode = not assocMode

					listKey = self.value
					dataType = EntryType(dataArray[i])
					i = i + 1
					sz = self._ReadValue(dataType, dataArray[i:])
					listVal = self.value
					i = i + sz
					value[listKey] = listVal
				else:
					value.append(self.value)
	
			self.value = value
			return i + 5			
	
		return 1


	def Size(self):
		return self.size + 4

class Entry:
	def __init__(self, entryData, offset, context):
		self.raw = entryData
		self.offset = offset
		self.header = EntryHeader(self, context)
		self.data = EntryData(self, context)

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
		self.context = ParserContext()
		self.entries = []

		while self.context.offset < len(self.data):
			self.context.entryOffset = self.context.offset
			entrySize = unpack('<i', self.data[self.context.offset:self.context.offset+4])[0]
			self.context.offset = self.context.offset + 4
			readEntry = (self.data[self.context.offset] == 1)
			self.context.offset = self.context.offset + 1

			if readEntry:
				self.entries.append(Entry(self.data[self.context.offset:self.context.offset + entrySize], self.context.offset - 5, self.context))
	
			self.context.offset = self.context.offset + entrySize
