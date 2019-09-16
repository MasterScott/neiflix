# -*- coding: utf-8 -*-
#Basado en la librería de MEGA que programó divadr y modificado por tonikelope para dar soporte a MEGACRYPTER

import threading
import Chunk
import ChunkDownloader
import ChunkWriter
import time
import os
import urllib2
from platformcode import platformtools,logger
from .crypto import *
try:
    from Crypto.Util import Counter
except ImportError:
    from Cryptodome.Util import Counter

CHUNK_WORKERS = 10

class Cursor(object):
    def __init__(self, file):
        self._file = file
        self.pos = 0
        self.pipe_r=None
        self.pipe_w=None
        self.chunk_writer=None
        self.chunk_downloaders=None
        self.turbo_lock=threading.Lock()
        self.initial_value = file.initial_value
        self.k = file.k


    def mega_request(self, offset):
        if not self._file.url:
            self._file.url = self._file.refreshMegaDownloadUrl()

        try:
            self.start_multi_download(offset)
            self.prepare_decoder(offset)
        except Exception:
            self.stop_multi_download()


    def start_multi_download(self, offset):

        self.pipe_r,self.pipe_w=os.pipe()

        self.chunk_writer = ChunkWriter.ChunkWriter(self, self.pipe_w, offset, self._file.size - 1)

        t = threading.Thread(target=self.chunk_writer.run)
        t.daemon = True
        t.start()

        self.chunk_downloaders = []

        for c in range(0,CHUNK_WORKERS):
            chunk_downloader = ChunkDownloader.ChunkDownloader(c+1, self.chunk_writer)
            self.chunk_downloaders.append(chunk_downloader)
            t = threading.Thread(target=chunk_downloader.run)
            t.daemon = True
            t.start()


    def workers_turbo(self, workers):

        if self.chunk_downloaders and self.turbo_lock.acquire(False):

            current_workers = len(self.chunk_downloaders)

            if not self.chunk_writer.exit and current_workers < workers:

                for c in range(current_workers, workers):
                    chunk_downloader = ChunkDownloader.ChunkDownloader(c+1, self.chunk_writer)
                    self.chunk_downloaders.append(chunk_downloader)
                    t = threading.Thread(target=chunk_downloader.run)
                    t.daemon = True
                    t.start()

                platformtools.dialog_notification("NEIFLIX", "MEGA PROXY (TURBO) MODE ENABLED")

            self.turbo_lock.release()


    def stop_multi_download(self):

        logger.info("Cursor stopping multi download!")

        if self.pipe_r:
            try:
                os.close(self.pipe_r)
            except Exception as e:
                logger.info(str(e))

        if self.pipe_w:
            try:
                os.close(self.pipe_w)
            except Exception as e:
                logger.info(str(e))
        try:
            if self.chunk_writer:
                self.chunk_writer.exit = True
        except Exception as e:
            logger.info(str(e))

        for c in self.chunk_downloaders:
            try:
                c.exit = True
            except Exception as e:
                logger.info(str(e))

        self.chunk_downloaders = None


    def read(self, n=None):
        if not self.pipe_r:
            return

        try:    
            res = os.read(self.pipe_r, n)
        except Exception:
            res = None

        if res:
            res = self.decode(res)
            self.pos += len(res)
        return res


    def seek(self, n):
        if n > self._file.size:
            n = self._file.size
        elif n < 0:
            raise ValueError('Seeking negative')
        self.mega_request(n)
        self.pos = n


    def tell(self):
        return self.pos


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_multi_download()

        self._file.cursors.remove(self)

        if len(self._file.cursors) == 0:
            self._file.cursor = False


    def decode(self, data):
        return self.decryptor.decrypt(data)


    def prepare_decoder(self, offset):
        initial_value = self.initial_value + int(offset / 16)
        self.decryptor = AES.new(a32_to_str(self.k), AES.MODE_CTR, counter=Counter.new(128, initial_value=initial_value))
        rest = offset - int(offset / 16) * 16
        if rest:
            self.decode(str(0) * rest)
