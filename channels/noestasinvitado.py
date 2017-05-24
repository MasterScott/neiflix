# -*- coding: utf-8 -*-
#------------------------------------------------------------
# pelisalacarta - XBMC Plugin
# Canal para noestasinvitado
# http://blog.tvalacarta.info/plugin-xbmc/pelisalacarta/
#------------------------------------------------------------
import re
import urlparse
import urllib
import urllib2
import json
import math
import os.path
import hashlib
import xbmc

from core import config
from core import logger
from core import scrapertools
from core.item import Item
from platformcode import platformtools

DEBUG = config.get_setting("debug")

def login():
    
    logger.info("channels.noestasinvitado login")
    
    data = scrapertools.cache_page("https://noestasinvitado.com/login/")
    
    LOGIN = config.get_setting("noestasinvitadouser", "noestasinvitado")
    
    PASSWORD = config.get_setting("noestasinvitadopassword", "noestasinvitado")
    
    post = "user="+LOGIN+"&passwrd="+PASSWORD+"&cookielength=-1"

    data = scrapertools.cache_page("https://noestasinvitado.com/login2/" , post=post)

    return True

def mainlist(item):
    logger.info("channels.noestasinvitado mainlist")
    
    itemlist = []

    if config.get_setting("noestasinvitadouser", "noestasinvitado") == "":
        itemlist.append( Item( channel=item.channel , title="Habilita tu cuenta en la configuración..." , action="settingCanal" , url="" ) )
    else:
        if login():
            itemlist.append( Item( channel=item.channel, title="Novedades Películas" , action="foro" , url="https://noestasinvitado.com/peliculas/" , folder=True, fa=True ) )
            itemlist.append( Item( channel=item.channel, title="Novedades Series" , action="foro" , url="https://noestasinvitado.com/series/" , folder=True ) )
            itemlist.append( Item( channel=item.channel, title="Novedades documetales" , action="foro" , url="https://noestasinvitado.com/documentales/" , folder=True ) )
            itemlist.append( Item( channel=item.channel, title="Novedades vídeos deportivos" , action="foro" , url="https://noestasinvitado.com/deportes/" , folder=True ) )
            itemlist.append( Item( channel=item.channel, title="Novedades ANIME" , action="foro" , url="https://noestasinvitado.com/anime/" , folder=True ) )
            itemlist.append( Item( channel=item.channel, title="Novedades XXX" , action="foro" , url="https://noestasinvitado.com/18-15/" , folder=True ) )
            itemlist.append( Item( channel=item.channel, title="Listados alfabéticos" , action="indices" , url="https://noestasinvitado.com/indices/" , folder=True ) )
            itemlist.append( Item( channel=item.channel, title="Buscar...", action="search", text_color="0xFFFF9933") )
        else:
            itemlist.append( Item( channel=item.channel , title="Usuario y/o password de NEI incorrecta, revisa la configuración..." , action="" , url="" , folder=False ) )
    return itemlist

def settingCanal(item):
    return platformtools.show_channel_settings()

def foro(item):
    logger.info("channels.noestasinvitado foro")

    itemlist=[]
    
    data = scrapertools.cache_page(item.url)

    mc_links=False

    final_item = False

    if '<h3 class="catbg">Subforos</h3>' in data:
        patron = '<a class="subje(.*?)t" href="([^"]+)" name="[^"]+">([^<]+)</a(>)' # HAY SUBFOROS
        action = "foro"
    elif '"subject windowbg4"' in data:
        patron = '<td class="subject windowbg4">.*?<div *?>.*?<span id="([^"]+)"> *?<a href="([^"]+)".*?>([^<]+)</a> *?</span>.*?"Ver +perfil +de +([^"]+)"'
        final_item=True
        action = "foro"
    else:
        mc_links = True
        itemlist = find_mc_links(item, data)

    if mc_links == False:

        matches = re.compile(patron,re.DOTALL).findall(data)
        
        for scrapedmsg,scrapedurl,scrapedtitle,uploader in matches:

            url = urlparse.urljoin(item.url,scrapedurl)

            scrapedtitle = scrapertools.htmlclean(scrapedtitle)

            if uploader != '>':
                title = scrapedtitle + " ("+uploader+")"
            else:
                title = scrapedtitle

            thumbnail = ""

            text_color = ""

            if final_item:

                content_title = extract_title(scrapedtitle)

                year = extract_year(scrapedtitle)

                if item.fa :

                    rating = get_filmaffinity_data(content_title, year)

                    if item.parent_title.startswith('Ultra HD '):
                        quality = 'UHD'
                    elif item.parent_title.startswith('HD '):
                        quality = 'HD'
                    else:
                        quality = 'SD'

                    if rating[0] != "SIN NOTA":
                        if float(rating[0]) >= 7.0:
                            rating_text = "[COLOR lightgreen][FA "+rating[0]+"][/COLOR]"
                        elif float(rating[0]) < 4.0:
                            rating_text = "[COLOR lightred][FA "+rating[0]+"][/COLOR]"
                        else:
                            rating_text = "[FA "+rating[0]+"]"
                    else:
                        rating_text = "[FA ---]"

                    title = "[COLOR darkorange][B]"+content_title+"[/B][/COLOR] ("+year+") ["+quality+"] [B]"+rating_text+ "[/B] ("+uploader+")"

                    if rating[1]:
                        thumbnail = rating[1].replace('msmall', 'large')
                    else:
                        thumbnail = ""

                item.infoLabels = {}

                item.infoLabels['year'] = year

            else:
                item.parent_title = title.strip()
                content_title =""

            itemlist.append( item.clone(action=action, title=title, url=url , thumbnail=thumbnail, folder=True, contentTitle=content_title) )

        
        patron = '<div class="pagelinks">Páginas:.*?\[<strong>[^<]+</strong>\].*?<a class="navPages" href="(?!\#bot)([^"]+)">[^<]+</a>.*?</div>'
        matches = re.compile(patron,re.DOTALL).findall(data)
        for match in matches:
            if len(matches) > 0:
                url = match
                title = "[B]>> Página Siguiente[/B]"
                thumbnail = ""
                plot = ""
                itemlist.append( item.clone(action="foro", title=title , url=url , thumbnail=thumbnail, folder=True) )

    return itemlist

def search(item, texto):
    
    itemlist = []

    if texto != "":
        texto = texto.replace(" ", "+")

    post = "advanced=1&search="+texto+"&searchtype=1&userspec=*&sort=relevance%7Cdesc&subject_only=1&minage=0&maxage=9999&brd%5B6%5D=6&brd%5B227%5D=227&brd%5B229%5D=229&brd%5B230%5D=230&brd%5B41%5D=41&brd%5B47%5D=47&brd%5B48%5D=48&brd%5B42%5D=42&brd%5B44%5D=44&brd%5B46%5D=46&brd%5B218%5D=218&brd%5B225%5D=225&brd%5B7%5D=7&brd%5B52%5D=52&brd%5B59%5D=59&brd%5B61%5D=61&brd%5B62%5D=62&brd%5B51%5D=51&brd%5B53%5D=53&brd%5B54%5D=54&brd%5B55%5D=55&brd%5B63%5D=63&brd%5B64%5D=64&brd%5B66%5D=66&brd%5B67%5D=67&brd%5B65%5D=65&brd%5B68%5D=68&brd%5B69%5D=69&brd%5B14%5D=14&brd%5B87%5D=87&brd%5B86%5D=86&brd%5B93%5D=93&brd%5B83%5D=83&brd%5B89%5D=89&brd%5B85%5D=85&brd%5B82%5D=82&brd%5B91%5D=91&brd%5B90%5D=90&brd%5B92%5D=92&brd%5B88%5D=88&brd%5B84%5D=84&brd%5B212%5D=212&brd%5B94%5D=94&brd%5B23%5D=23&submit=Buscar"

    data = scrapertools.cache_page("https://noestasinvitado.com/search2/" , post=post)

    patron = '<h5>[^<>]*<a[^<>]+>.*?</a>[^<>]*?<a +href="([^"]+)">(.*?)</a>[^<>]*</h5>[^<>]*<span[^<>]*>.*?<a[^<>]*"Ver +perfil +de +([^"]+)"'

    matches = re.compile(patron,re.DOTALL).findall(data)
        
    for scrapedurl, scrapedtitle, uploader in matches:

        url = urlparse.urljoin(item.url,scrapedurl)

        scrapedtitle = scrapertools.htmlclean(scrapedtitle) 

        title = scrapedtitle + " ["+uploader+"]"

        thumbnail = ""

        year = extract_year(scrapedtitle)

        content_title = extract_title(scrapedtitle)

        item.infoLabels = {}
        
        item.infoLabels['year'] = year

        itemlist.append( item.clone(action="foro", title=title , url=url , thumbnail=thumbnail, contentTitle=content_title, folder=True, text_color="") )

    patron = '\[<strong>[0-9]+</strong>\][^<>]*<a class="navPages" href="([^"]+)">'
    
    matches = re.compile(patron, re.DOTALL).search(data)

    if matches:

        url=matches.group(1)
        title = ">> Página Siguiente"
        thumbnail = ""
        plot = ""
        itemlist.append( item.clone(action="search_pag", title=title, url=url, thumbnail=thumbnail, folder=True, text_color='0xFFFF9933') )

    return itemlist


def search_pag(item):

    itemlist = []

    data = scrapertools.cache_page(item.url)

    patron = '<h5>[^<>]*<a[^<>]+>.*?</a>[^<>]*?<a +href="([^"]+)">(.*?)</a>[^<>]*</h5>[^<>]*<span[^<>]*>.*?<a[^<>]*"Ver +perfil +de +([^"]+)"'

    matches = re.compile(patron,re.DOTALL).findall(data)
        
    for scrapedurl, scrapedtitle, uploader in matches:

        url = urlparse.urljoin(item.url,scrapedurl)

        scrapedtitle = scrapertools.htmlclean(scrapedtitle) 

        title = scrapedtitle + " ["+uploader+"]"

        thumbnail = ""

        year = extract_year(scrapedtitle)

        content_title = extract_title(scrapedtitle)

        item.infoLabels = {}
        
        item.infoLabels['year'] = year

        itemlist.append( item.clone(action="foro", title=title , url=url , thumbnail=thumbnail, contentTitle=content_title, folder=True, text_color="") )

    patron = '\[<strong>[0-9]+</strong>\][^<>]*<a class="navPages" href="([^"]+)">'
    
    matches = re.compile(patron, re.DOTALL).search(data)

    if matches:

        url=matches.group(1)
        title = ">> Página Siguiente"
        thumbnail = ""
        plot = ""
        itemlist.append( item.clone(action="search_pag", title=title, url=url, thumbnail=thumbnail, folder=True, text_color='0xFFFF9933') )

    return itemlist


def indices(item):

    itemlist=[]

    categories = ['Películas HD Español', 'Películas HD VO', 'Películas SD Español', 'Películas SD VO', 'Series HD Español', 'Series HD VO', 'Series SD Español', 'Series SD VO', 'Películas Anime Español', 'Películas Anime VO', 'Series Anime Español', 'Series Anime VO', 'Películas clásicas', 'Deportes', 'Películas XXX HD', 'Películas XXX SD', 'Vídeos XXX HD', 'Vídeos XXX SD']

    for cat in categories:
        itemlist.append( Item( channel=item.channel , title=cat , action="gen_index" , url="https://noestasinvitado.com/indices/" , folder=True ) )

    return itemlist

def gen_index(item):

    categories = {'Películas HD Español': 47, 'Películas HD VO': 48, 'Películas SD Español': 44, 'Películas SD VO': 42, 'Series HD Español': 59, 'Series HD VO': 61, 'Series SD Español': 53, 'Series SD VO': 54, 'Películas Anime Español' : 66, 'Películas Anime VO' : 67, 'Series Anime Español' : 68, 'Series Anime VO' : 69, 'Películas clásicas' : 218, 'Deportes' : 23, 'Películas XXX HD': 182, 'Películas XXX SD': 183, 'Vídeos XXX HD': 185, 'Vídeos XXX SD': 186}

    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'Ñ', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0-9']
    
    itemlist=[]

    start = 1

    for letter in letters:
        itemlist.append( Item( channel=item.channel , title="%s (Letra %s)" % (item.title, letter) , action="indice_links" , url="https://noestasinvitado.com/indices/?id=%d;start=%d" % (categories[item.title], start) , folder=True ) )
        start = start + 1

    return itemlist

def get_mc_links_group(item):

    itemlist=[]

    id = item.mc_group_id

    filename_hash = xbmc.translatePath("special://home/temp/kodi_nei_mc_"+hashlib.sha1(item.channel+item.url+id).hexdigest())

    if os.path.isfile(filename_hash):

        file = open(filename_hash, "r")

        i = 1

        for line in file:

            line = line.rstrip()

            if i > 1:

                url = line

                url_split = url.split('#')

                name = url_split[1]

                size = url_split[2]

                title = name+' ['+str(format_bytes(float(size)))+']'

                itemlist.append(Item(channel=item.channel, action="play", server='mega', title=title, url=url, parentContent=item, folder=False))

            else:

                links_hash = line

                data = scrapertools.cache_page("https://noestasinvitado.com/gen_mc.php?id="+id+"&raw=1")

                patron='(.*? *?\[[0-9.]+ *?.*?\]) *?(https://megacrypter.noestasinvitado.com/.+)'

                matches = re.compile(patron).findall(data)

                if matches:

                    hasheable = ""

                    for title,url in matches:
                        hasheable+=title

                    links_hash2 = hashlib.sha1(hasheable).hexdigest()

                    if links_hash != links_hash2:

                        file.close()

                        os.remove(filename_hash)

                        return get_mc_links_group(item)
                else:
                        file.close()

                        return itemlist

            i+=1

        file.close()

    else:

        data = scrapertools.cache_page("https://noestasinvitado.com/gen_mc.php?id="+id+"&raw=1")

        patron='(.*? *?\[[0-9.]+ *?.*?\]) *?(https://megacrypter.noestasinvitado.com/.+)'

        matches = re.compile(patron).findall(data)

        if matches:
            
            hasheable = ""

            for title,url in matches:
                hasheable+=title

            links_hash = hashlib.sha1(hasheable).hexdigest()

            compress_pattern = re.compile('\.(zip|rar|rev)$', re.IGNORECASE)

            file = open(filename_hash, "w+")

            file.write((links_hash+"\n").encode('utf-8'))

            for title, url in matches:
                
                url_split = url.split('/!')
                
                mc_api_url = url_split[0]+'/api'
                
                mc_info_res = mc_api_req(mc_api_url, {'m':'info', 'link': url})
                
                name = mc_info_res['name'].replace('#', '')
                
                size = mc_info_res['size']
                
                key = mc_info_res['key']
                
                noexpire = mc_info_res['expire'].split('#')[1]

                compress = compress_pattern.search(name)

                if compress:
                    
                    itemlist.append( Item( channel=item.channel , title="ESTE VÍDEO ESTÁ COMPRIMIDO Y NO ES COMPATIBLE (habla con el uploader para que lo suba sin comprimir).", text_color="0xFFFF0000", action="" , url="" , folder=False ) )
                    
                    break
                
                else:

                    title = name+' ['+str(format_bytes(size))+']'

                    url=url+'#'+name+'#'+str(size)+'#'+key+'#'+noexpire

                    file.write((url+"\n").encode('utf-8'))

                    itemlist.append(Item(channel=item.channel, action="play", server='mega', title=title, url=url, parentContent=item, folder=False))

            file.close()

    return itemlist

def find_mc_links(item, data):

    msg_id = re.compile('subject_([0-9]+)', re.IGNORECASE).search(data)

    if msg_id:

        thanks_match = re.compile('/\?action\=thankyou;msg\='+msg_id.group(1), re.IGNORECASE).search(data)

        if thanks_match:
            data = scrapertools.cache_page(item.url+thanks_match.group(0))

    itemlist=[]

    patron='id="mc_link_.*?".*?data-id="(.*?)"'

    matches = re.compile(patron,re.DOTALL).findall(data)

    if matches:

        if len(matches) > 1:

            i = 1

            for id in matches:

                itemlist.append(Item(channel=item.channel, action="get_mc_links_group", title='['+str(i)+'/'+str(len(matches))+'] '+item.title, url=item.url, mc_group_id=id, folder=True))

                i = i + 1
        else:
            itemlist = get_mc_links_group(Item(channel=item.channel, action='', title='', url=item.url, mc_group_id=matches[0], folder=True))
    else:

        filename_hash = xbmc.translatePath("special://home/temp/kodi_nei_mc_"+hashlib.sha1(item.channel+item.url).hexdigest())

        if os.path.isfile(filename_hash):

            file = open(filename_hash, "r")

            i = 1

            for line in file:

                line = line.rstrip()

                if i > 1:

                    url = line

                    url_split = url.split('#')

                    name = url_split[1]

                    size = url_split[2]

                    title = name+' ['+str(format_bytes(float(size)))+']'

                    itemlist.append(Item(channel=item.channel, action="play", server='mega', title=title, url=url, parentContent=item, folder=False))

                else:

                    links_hash = line

                    patron='https://megacrypter.noestasinvitado.com/[!0-9a-zA-Z_/-]+'

                    matches = re.compile(patron).findall(data)

                    if matches:

                        links_hash2 = hashlib.sha1("".join(matches)).hexdigest()

                        if links_hash != links_hash2:

                            file.close()

                            os.remove(filename_hash)

                            return find_mc_links(item, data)
                    else:
                        
                        file.close()

                        return itemlist

                i+=1

            file.close()

        else:

            urls=[]

            patron='https://megacrypter.noestasinvitado.com/[!0-9a-zA-Z_/-]+'

            matches = re.compile(patron).findall(data)

            if matches:

                compress_pattern = re.compile('\.(zip|rar|rev)$', re.IGNORECASE)

                file = open(filename_hash, "w+")

                links_hash = hashlib.sha1("".join(matches)).hexdigest()

                file.write((links_hash+"\n").encode('utf-8'))

                for url in matches:

                    if url not in urls:
                        
                        urls.append(url)
                        
                        url_split = url.split('/!')
                        
                        mc_api_url = url_split[0]+'/api'
                        
                        mc_info_res = mc_api_req(mc_api_url, {'m':'info', 'link': url})
                        
                        name = mc_info_res['name'].replace('#', '')
                        
                        size = mc_info_res['size']
                        
                        key = mc_info_res['key']

                        if mc_info_res['expire']:
                            noexpire = mc_info_res['expire'].split('#')[1]
                        else:
                            noexpire = ''

                        compress = compress_pattern.search(name)

                        if compress:
                            itemlist.append( Item( channel=item.channel , title="ESTE VÍDEO ESTÁ COMPRIMIDO Y NO ES COMPATIBLE (habla con el uploader para que lo suba sin comprimir).", text_color="0xFFFF0000", action="" , url="" , folder=False ) )
                            break
                        else:
                            title = name+' ['+str(format_bytes(size))+']'
                            url=url+'#'+name+'#'+str(size)+'#'+key+'#'+noexpire
                            file.write((url+"\n").encode('utf-8'))
                            itemlist.append(Item(channel=item.channel, action="play", server='mega', title=title, url=url, parentContent=item, folder=False))

                file.close()

    return itemlist

def indice_links(item):

    itemlist=[]

    data = scrapertools.cache_page(item.url)

    patron = '<tr class="windowbg2">[^<>]*<td[^<>]*>[^<>]*<img[^<>]*>[^<>]*</td>[^<>]*<td>[^<>]*<a href="([^"]+)">(.*?)</a>[^<>]*</td>[^<>]*<td[^<>]*>[^<>]*<a[^<>]*>([^<>]+)'

    matches = re.compile(patron,re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, uploader in matches:

        url = urlparse.urljoin(item.url, scrapedurl)

        scrapedtitle = scrapertools.htmlclean(scrapedtitle)

        content_title = extract_title(scrapedtitle)

        year = extract_year(scrapedtitle)

        if item.title.find('Películas') != -1:

            if item.title.find(' HD ') != -1:
                quality = 'HD'
            else:
                quality = 'SD'

            title = content_title+" ("+year+") ["+quality+"] ("+uploader+")"
        else:
            title = scrapedtitle

        thumbnail = ""

        item.infoLabels = {}
        
        item.infoLabels['year'] = year

        itemlist.append( item.clone(action="foro", title=title, url=url , thumbnail=thumbnail, folder=True, contentTitle=content_title) )

    return itemlist

def post(url, data):
    
    import ssl
    from functools import wraps
    def sslwrap(func):
        @wraps(func)
        def bar(*args, **kw):
            kw['ssl_version'] = ssl.PROTOCOL_TLSv1
            return func(*args, **kw)
        return bar

    ssl.wrap_socket = sslwrap(ssl.wrap_socket)

    request = urllib2.Request(url, data=data, headers={"User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36"})

    contents = urllib2.urlopen(request).read()

    return contents

def mc_api_req(api_url, req):

    res = post(api_url, json.dumps(req))

    return json.loads(res)


def format_bytes(bytes, precision=2):

    units = ['B', 'KB', 'MB', 'GB', 'TB']

    bytes = max(bytes, 0)

    pow = min(math.floor(math.log(bytes if bytes else 0, 1024)), len(units) - 1)

    bytes = float(bytes) / (1 << int(10 * pow))

    return str(round(bytes, precision))+' '+units[int(pow)]

def extract_title(title):

    pattern = re.compile('^[^\[\]\(\)]+', re.IGNORECASE)

    res = pattern.search(title)

    if res:

        return res.group(0)

    else:

        return ""

def extract_year(title):

    pattern = re.compile('([0-9]{4})[^p]', re.IGNORECASE)

    res = pattern.search(title)

    if res:

        return res.group(1)

    else:

        return ""

def get_filmaffinity_data(title, year):

    url = "https://www.filmaffinity.com/es/advsearch.php?stext="+title.replace(' ','+')+"&stype%5B%5D=title&country=&genre=&fromyear="+year+"&toyear="+year

    logger.info(url)

    data = scrapertools.cache_page(url)

    res = re.compile("< *?div +class *?= *?\"avgrat-box\" *?> *?([0-9,]+) *?<",re.DOTALL).search(data)

    if res:

        res_thumb = re.compile("https://pics\\.filmaffinity\\.com/[^\"]+-msmall\\.jpg",re.DOTALL).search(data)

        if res_thumb:
            thumb_url = res_thumb.group(0)
        else:
            thumb_url = None

        return [res.group(1).replace(',','.'), thumb_url]

    else:

        url = "https://www.filmaffinity.com/es/advsearch.php?stext="+title.replace(' ','+')+"&stype%5B%5D=title&country=&genre="

        data = scrapertools.cache_page(url)

        res_thumb = re.compile("https://pics\\.filmaffinity\\.com/[^\"]+-msmall\\.jpg",re.DOTALL).search(data)

        if res_thumb:
            thumb_url = res_thumb.group(0)
        else:
            thumb_url = None

        res = re.compile("< *?div +class *?= *?\"avgrat-box\" *?> *?([0-9,]+) *?<",re.DOTALL).search(data)

        if res:

            return [res.group(1).replace(',','.'), thumb_url]

        else:

            return ["SIN NOTA", thumb_url]