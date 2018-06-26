# -*- coding: utf-8 -*-

class Chunk():
	
	def __init__(self, offset, size):
		self.offset = offset
		self.size = size
		self.data = None
