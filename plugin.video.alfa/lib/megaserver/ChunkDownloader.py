# -*- coding: utf-8 -*-

import threading
import urllib2
import Chunk
import time
import MegaProxyManager

MAX_CHUNK_BUFFER_SIZE = 20
BLOCK_SIZE = 16*1024
WORKERS_TURBO = 16

class ChunkDownloader():

	def __init__(self, id, chunk_writer):
		self.id = id
		self.chunk_writer = chunk_writer
		self.proxy_manager = MegaProxyManager.MegaProxyManager()
		self.url = self.chunk_writer.cursor._file.url
		self.cv_new_url = threading.Condition()
		self.proxy = None
		self.exit = False


	def run(self):

		print("ChunkDownloader [%d] HELLO!" % self.id)

		time.sleep((self.id - 1)*0.5)

		error = False

		error509 = False

		offset = -1

		turbo = False

		while not self.chunk_writer.exit and not self.exit:

			try:

				while not self.chunk_writer.exit and not self.exit and len(self.chunk_writer.queue) >= MAX_CHUNK_BUFFER_SIZE:
					print("ChunkDownloader %d me duermo porque la cola está llena!" % self.id)
					with self.chunk_writer.cv_queue_full:
						self.chunk_writer.cv_queue_full.wait(1)

				if not self.chunk_writer.exit and not self.exit:

					if offset<0 or (not error and not error509):
						offset = self.chunk_writer.nextOffset()
					elif self.proxy:
						print("ChunkDownloader[%d] bloqueando proxy %s" % (self.id, self.proxy))
						self.proxy_manager.block_proxy(self.proxy)
						self.proxy = self.proxy_manager.get_fastest_proxy()
					elif error509:
						if not turbo:
							self.chunk_writer.cursor.workers_turbo(WORKERS_TURBO)
							turbo = True

						self.proxy = self.proxy_manager.get_fastest_proxy()

					error = False

					error509 = False

					if offset >= 0:

						chunk = Chunk.Chunk(offset, self.chunk_writer.calculateChunkSize(offset))

						print("ChunkDownloader[%d] leyendo CHUNK %d" % (self.id, offset))

						try:

							print("ChunkDownloader[%d] leyendo %s" % (self.id, self.url+('/%d-%d' % (int(offset), int(offset)+chunk.size-1))))

							req = urllib2.Request(self.url+('/%d-%d' % (int(offset), int(offset)+chunk.size-1)))

							if self.proxy:
								req.set_proxy(self.proxy, 'http')
								print("ChunkDownloader[%d] usando proxy %s" % (self.id, self.proxy))

							connection = urllib2.urlopen(req)

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
									error = True
								else:
									self.chunk_writer.queue[chunk.offset]=chunk
									with self.chunk_writer.cv_new_element:
										self.chunk_writer.cv_new_element.notifyAll()

						except urllib2.HTTPError as err:
							error = True
							
							print("ChunkDownloader[%d] HTTP ERROR %d" % (self.id, err.code))

							if err.code == 509:
								error509 = True
							elif err.code == 403:
								if not self.chunk_writer.cursor._file.refreshMegaDownloadUrl(self.cv_new_url):
									with self.cv_new_url:
										self.cv_new_url.wait(5)
									
								self.url = self.chunk_writer.cursor._file.url
							elif err.code == 503 and offset >= 0:
								self.chunk_writer.offset_rejected.put(offset)
							
								offset=-1
								
								with self.chunk_writer.cv_error_503:
									print("ChunkDownloader[%d] me duermo 5 segundos..." % self.id)
									self.chunk_writer.cv_error_503.wait(5)

					else:
						print("ChunkDownloader[%d] END OFFSET" % self.id)
						self.exit = True

			except Exception as e:
				print("ChunkDownloader[%d] %s" % (self.id, str(e)))
				
				if offset >= 0:
					self.chunk_writer.offset_rejected.put(offset)
				
				self.exit = True

		print("ChunkDownloader [%d] BYE BYE" % self.id)

