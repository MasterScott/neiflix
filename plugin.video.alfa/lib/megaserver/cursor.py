# -*- coding: utf-8 -*-
#Basado en la librería de MEGA que programó divadr y modificado por tonikelope para dar soporte a MEGACRYPTER

import threading
import Chunk
import ChunkDownloader
import ChunkWriter
import os
import urllib2
from .crypto import *
try:
    from Crypto.Util import Counter
except ImportError:
    from Cryptodome.Util import Counter

MAX_CHUNK_WORKERS = 4

class Cursor(object):
    def __init__(self, file):
        self._file = file
        self.pos = 0
        self.pipe_r=None
        self.pipe_w=None
        self.chunk_writer=None
        self.chunk_downloaders=[]
        self.initial_value = file.initial_value
        self.k = file.k


    def mega_request(self, offset, retry=False):
        if not self._file.url or retry:
            self._file.url = self.get_new_url_from_api()

        try:
            self.start_multi_download(offset)
            self.prepare_decoder(offset)
        except Exception:
            self.stop_multi_download()


    def get_new_url_from_api():
        if self._file.folder_id:
            file = self._file._client.api_req({"a": "g", "g": 1, "n": self._file.file_id}, "&n=" + self._file.folder_id)
            return file["g"]
        elif self._file.file_id != -1:
            file = self._file._client.api_req({'a': 'g', 'g': 1, 'p': self._file.file_id})
            return file["g"]
        else:
            mc_req_data = {'m': 'dl', 'link': self._file.info['mc_link']}

            if 'noexpire' in self._file.info:
                mc_req_data['noexpire'] = self._file.info['noexpire']

            if 'reverse' in self._file.info:
                mc_req_data['reverse'] = self._file.info['reverse']

            if 'sid' in self._file.info:
                mc_req_data['sid'] = self._file.info['sid']

            mc_dl_res=self._file._client.mc_api_req(self._file.info['mc_api_url'], mc_req_data)

            return mc_dl_res['url']


    def start_multi_download(self, offset):

        self.pipe_r,self.pipe_w=os.pipe()

        self.chunk_writer = ChunkWriter.ChunkWriter(self, self.pipe_w, self._file.url, offset, self._file.size - 1)

        t = threading.Thread(target=self.chunk_writer.run)
        t.daemon = True
        t.start()

        self.chunk_downloaders = []

        for c in range(0,MAX_CHUNK_WORKERS):
            chunk_downloader = ChunkDownloader.ChunkDownloader(c+1, self.chunk_writer)
            self.chunk_downloaders.append(chunk_downloader)
            t = threading.Thread(target=chunk_downloader.run)
            t.daemon = True
            t.start()


    def stop_multi_download(self):

        if self.pipe_r:
            try:
                os.close(self.pipe_r)
            except Exception as e:
                print(str(e))

        if self.pipe_w:
            try:
                os.close(self.pipe_w)
            except Exception as e:
                print(str(e))
        try:
            if self.chunk_writer:
                self.chunk_writer.exit = True
        except Exception as e:
            print(str(e))

        for c in self.chunk_downloaders:
            try:
                c.exit = True
            except Exception as e:
                print(str(e))


    def read(self, n=None):
        if not self.pipe_r:
            return

        try:    
            res = os.read(self.pipe_r, n)
        except Exception:
            pass

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
