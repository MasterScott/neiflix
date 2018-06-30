# -*- coding: utf-8 -*-
#Basado en la librería de MEGA que programó divadr y modificado por tonikelope para dar soporte a MEGACRYPTER

import urllib2
import threading
import MegaProxyManager
from cursor import Cursor

class File(object):
    def __init__(self, info, file_id, key, file, client, folder_id=None):
        self._client = client
        self.folder_id = folder_id
        self.file_id = file_id
        self.cursor = False
        self.cursors = []
        self.key = key
        self.file = file
        self.info = info
        self.name = info["n"]
        self.size = file["s"]
        self.request = None
        self.k = self.key[0] ^ self.key[4], self.key[1] ^ self.key[5], self.key[2] ^ self.key[6], self.key[3] ^ \
            self.key[7]
        self.iv = self.key[4:6] + (0, 0)
        self.initial_value = (((self.iv[0] << 32) + self.iv[1]) << 64)
        if not self.folder_id:
            self.url = self.file["g"]
        else:
            self.url = None
        self.url_lock = threading.Lock()
        self.proxy_manager = MegaProxyManager.MegaProxyManager()
        self.refreshMegaDownloadUrl()


    def create_cursor(self, offset):
        c = Cursor(self)
        c.seek(offset)
        self.cursor = True
        self.cursors.append(c)
        return c


    def checkMegaDownloadUrl(self, url):

        print("Checking MEGA DL URL %s" % url)

        error509 = False

        proxy = None

        error = False

        while not error:

            if error509:
                if proxy:
                    self.proxy_manager.block_proxy(proxy)

                proxy = self.proxy_manager.get_fastest_proxy()

            error509 = False


            try:

                req = urllib2.Request(url+'/0-0')

                if proxy:
                    req.set_proxy(proxy, 'http')

                connection = urllib2.urlopen(req, timeout=15)

                connection.read()

                print("MEGA DL URL IS OK!")
                return True

            except urllib2.HTTPError as err:
                print("CHECKING MEGA DL URL ERROR %d" % err.code)

                if err.code == 509:
                    error509 = True
                else:
                    error = True
            except urllib2.socket.timeout:
                error = True


    def refreshMegaDownloadUrl(self, cv_new_url=None):
        if self.url_lock.acquire(False):

            while not self.url or not self.checkMegaDownloadUrl(self.url):
                self.url=self.get_new_url_from_api()

            self.url_lock.release()

            if cv_new_url:
                with cv_new_url:
                    cv_new_url.notifyAll()

            return True

        return False

    def get_new_url_from_api(self):
        if self.folder_id:
            file = self._client.api_req({"a": "g", "g": 1, "n": self.file_id}, "&n=" + self.folder_id)
            return file["g"]
        elif self.file_id != -1:
            file = self._client.api_req({'a': 'g', 'g': 1, 'p': self.file_id})
            return file["g"]
        else:
            mc_req_data = {'m': 'dl', 'link': self.info['mc_link']}

            if 'noexpire' in self.info:
                mc_req_data['noexpire'] = self.info['noexpire']

            if 'reverse' in self.info:
                mc_req_data['reverse'] = self.info['reverse']

            if 'sid' in self.info:
                mc_req_data['sid'] = self.info['sid']

            mc_dl_res=self._client.mc_api_req(self.info['mc_api_url'], mc_req_data)

            return mc_dl_res['url']

