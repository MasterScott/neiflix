# -*- coding: utf-8 -*-

import threading
import MegaProxyManager
import Queue
import Chunk
import os

CHUNK_SIZE = 1048576

class ChunkWriter():

	def __init__(self, cursor, pipe, start_offset, end_offset):
		self.cursor = cursor
		self.pipe = pipe
		self.start_offset = start_offset
		self.end_offset = end_offset
		self.queue = {}
		self.cv_queue_full = threading.Condition()
		self.cv_new_element = threading.Condition()
		self.cv_error_503 = threading.Condition()
		self.bytes_written = start_offset
		self.exit = False
		self.next_offset_required = start_offset
		self.chunk_offset_lock = threading.Lock()
		self.proxy_manager = MegaProxyManager.MegaProxyManager()
		self.offset_rejected = Queue.Queue()


	def run(self):

		print("ChunkWriter HELLO!")

		while not self.exit and self.bytes_written < self.end_offset and self.cursor._file._client.running:

			while not self.exit and self.cursor._file._client.running and self.bytes_written < self.end_offset and self.bytes_written in self.queue:

				current_chunk = self.queue.pop(self.bytes_written)

				try:
					os.write(self.pipe, current_chunk.data)

					print("ChunkWriter chunk %d escrito"%current_chunk.offset)

					self.bytes_written+=current_chunk.size

					with self.cv_queue_full:
						self.cv_queue_full.notifyAll()

				except Exception as e:
					print(str(e))

			if not self.exit and self.cursor._file._client.running and self.bytes_written < self.end_offset:

				print("ChunkWriter me duermo hasta que haya chunks nuevos en la cola")

				with self.cv_new_element:
					self.cv_new_element.wait(1)

		self.exit = True

		with self.cv_error_503:
			self.cv_error_503.notifyAll()

		print("ChunkWriter BYE BYE")


	def nextOffset(self):
		
		if not self.offset_rejected.empty():
			next_offset = self.offset_rejected.get()
		else:
			self.chunk_offset_lock.acquire()

			next_offset = self.next_offset_required

			self.next_offset_required = self.next_offset_required + CHUNK_SIZE if self.next_offset_required + CHUNK_SIZE < self.end_offset else -1;

			self.chunk_offset_lock.release()

		return next_offset


	def calculateChunkSize(self, offset):
		return min(CHUNK_SIZE, self.end_offset - offset + 1) if offset <= self.end_offset else -1


