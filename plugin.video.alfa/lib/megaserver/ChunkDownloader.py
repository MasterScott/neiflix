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

					if not error:
						offset = self.chunk_writer.nextOffset()
					elif self.proxy:
						print("ChunkDownloader[%d] bloqueando proxy %s" % (self.id, self.proxy))
						self.proxy_manager.block_proxy(self.proxy)
						self.proxy = self.proxy_manager.get_fastest_proxy()
					
					if error509:
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

							if connection.getcode() == 200 or connection.getcode() == 206:

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

							elif connection.getcode() == 509:
								print("HTTP ERROR %d" % connection.getcode())
								error = True
								error509 = True
							else:
								print("HTTP ERROR %d" % connection.getcode())
								error = True

								if connection.getcode() == 403:
									if not self.chunk_writer.cursor._file.refreshMegaDownloadUrl():
										time.sleep(5)
									
									self.url = self.chunk_writer.cursor._file.url
								elif connection.getcode() == 503:
									time.sleep(1)

						except Exception as e:
							print(str(e))
							error = True
					else:
						self.exit = True

			except Exception as e:
				print(str(e))

		print("ChunkDownloader [%d] BYE BYE" % self.id)

