# -*- coding: utf-8 -*-

import threading
import urllib2
import Chunk
import time

MAX_CHUNK_BUFFER_SIZE = 20
BLOCK_SIZE = 16*1024

class ChunkDownloader():

	def __init__(self, id, chunk_writer):
		self.id = id
		self.chunk_writer = chunk_writer
		self.exit = False


	def run(self):

		print("ChunkDownloader [%d] HELLO!" % self.id)

		url = self.chunk_writer.url

		error = False

		error509 = False

		offset = -1

		while not self.chunk_writer.exit and not self.exit:

			while not self.chunk_writer.exit and not self.exit and len(self.chunk_writer.queue) >= MAX_CHUNK_BUFFER_SIZE:
				print("ChunkDownloader %d me duermo porque la cola está llena!" % self.id)
				with self.chunk_writer.cv_queue_full:
					self.chunk_writer.cv_queue_full.wait(1)

			if not self.chunk_writer.exit and not self.exit:

				if not error:
					offset = self.chunk_writer.nextOffset()
				else:
					url = self.chunk_writer.url

				if offset >= 0:

					chunk = Chunk.Chunk(offset, self.chunk_writer.calculateChunkSize(offset))

					print("ChunkDownloader[%d] leyendo CHUNK %d" % (self.id, offset))

					error = False

					erro509 = False

					try:

						req = urllib2.Request(url)

						req.headers['Range'] = 'bytes=%d-%d' % (int(offset), int(offset)+chunk.size-1)

						connection = urllib2.urlopen(req)

						if connection.getcode() == 206:

							bytes_read = 0

							chunk.data = bytearray()

							while bytes_read < chunk.size and not self.chunk_writer.exit and not self.exit:
								to_read = min(BLOCK_SIZE, chunk.size - bytes_read)

								try:
									chunk.data+=connection.read(to_read)
									bytes_read+=to_read
								except Exception:
									pass

							if not self.chunk_writer.exit and not self.exit:

								if len(chunk.data) != chunk.size:
									self.error = True
									time.sleep(5)
								else:
									self.chunk_writer.queue[chunk.offset]=chunk
									with self.chunk_writer.cv_new_element:
										self.chunk_writer.cv_new_element.notifyAll()
						else:
							print("HTTP ERROR %d" % connection.getcode())
							self.error = True

							if connection.getcode() == 403:
								self.chunk_writer.cursor._file.url = self.chunk_writer.cursor.get_new_url_from_api()
							
							time.sleep(5)

					except Exception as e:
						print(str(e))
						self.error = True
						time.sleep(5)
				else:
					self.exit = True

		print("ChunkDownloader [%d] BYE BYE" % self.id)

