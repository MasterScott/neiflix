# -*- coding: utf-8 -*-
import json
import random
from core import httptools
from core import scrapertools
from platformcode import platformtools, logger

files = None

def test_video_exists(page_url):
    
    from megaserver import Client
    c = Client(url=page_url, is_playing_fnc=platformtools.is_playing)
    global files
    files = c.get_files()
    if files == 509:
        msg1 = "[B][COLOR tomato]El video excede el limite de visionado diario que Mega impone a los usuarios Free."
        msg1 += " Prueba en otro servidor o canal.[/B][/COLOR]"
        return False, msg1
    elif isinstance(files, (int, long)):
        return False, "Error codigo %s" % str(files)

    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    page_url = page_url.replace('/embed#', '/#')
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    # si hay mas de 5 archivos crea un playlist con todos
    # Esta función (la de la playlist) no va, hay que ojear megaserver/handler.py aunque la llamada este en client.py
    if len(files) > 5:
        media_url = c.get_play_list()
        video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [mega]", media_url])
    else:
        for f in files:
            media_url = f["url"]
            video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [mega]", media_url])

    return video_urls
