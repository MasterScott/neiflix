# -*- coding: utf-8 -*-

import urllib2
import collections
import time

PROXY_LIST_URL='https://raw.githubusercontent.com/tonikelope/megabasterd/proxy_list/proxy_list.txt'
PROXY_BLOCK_TIME = 30

class MegaProxyManager():

	def __init__(self):
		self.proxy_list=None

	
	def refresh_proxy_list(self):

		self.proxy_list = collections.OrderedDict()
		
		req = urllib2.Request(PROXY_LIST_URL)

		connection = urllib2.urlopen(req)

		proxy_data = connection.read()

		for p in proxy_data.split('\n'):
			self.proxy_list[p]=time.time()

		if len(self.proxy_list) == 0:
			self.proxy_list = None


	def get_fastest_proxy(self):

		if not self.proxy_list:
			self.refresh_proxy_list()
			return self.proxy_list.iteritems().next()[0] if self.proxy_list else None
		else:
			for proxy,timestamp in self.proxy_list.iteritems():
				if time.time() > timestamp:
					return proxy

			self.refresh_proxy_list()

			return self.proxy_list.iteritems().next()[0] if self.proxy_list else None


	def block_proxy(self,proxy):

		if not self.proxy_list:
			self.refresh_proxy_list()

		if proxy in self.proxy_list:
			self.proxy_list[proxy] = time.time() + PROXY_BLOCK_TIME
