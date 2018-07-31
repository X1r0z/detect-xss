from bs4 import BeautifulSoup as bs
from urllib.parse import urlsplit
import requests
import random
import string
import re
import os
import sys

url = 'http://127.0.0.1:8000/xss-example';

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
            url = murl.split('//',1)[0] + '//' + host + '/' + dirname + '/' + el['href']
        if url.find('?') != -1:
            url = url.split('?')[0]
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
    rest_links = dict()
    response = requests.get(murl)
    html = bs(response.text,'html.parser')
    a = html.find_all(name='a')
    for el in a:
        parse = urlsplit(el['href'])
        host = murl.split('//',1)[1].split('/',1)[0]
        path = parse[2]
        dirname = os.path.dirname(murl.split('//',1)[1].split('/',1)[1])
        if el['href'].startswith('http'):
            url = el['href']
        elif el['href'].startswith('//'):
            url = murl.split('//',1)[0] + el['href']
        elif el['href'].startswith('/'):
            url = murl.split('//',1)[0] + '//' + host + el['href']
        else:
            url = murl.split('//',1)[0] + '//' + host + '/' + dirname + '/' + el['href']
        if url.find('?') != -1:
            url = url.split('?')[0]
        plist = path.split('/')
        for p in plist:
            fuzz = plist
            rnd = ''.join(random.sample(string.ascii_letters,8))
            fuzz[plist.index(p)] = rnd
            req = '/'.join(fuzz)
            print(req)
            rurl = murl.split('//',1)[0] + host + '/' + req
            print(rurl)
            response = requests.get(rurl)
            if response.text.find(rnd) != -1:
                print(path,'is dynamic')
            if not url in rest_links:
                rest_links[url] = dict()
            if not 'get' in rest_links[url]:
                rest_links[url]['get'] = list()
            rest_links[url]['get'].append(p)
    return rest_links


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
            url = murl.split('//',1)[0] + '//' + host + '/' + dirname + '/' + f['action']
        tags = f.find_all(name='input')
        print('action:',url)
        print('method:',f['method'])
        if not url in form_links:
            form_links[url] = dict()
        if not f['method'] in form_links[url]:
            form_links[url][f['method']] = list()
        for el in tags:
            if el['type'] != 'submit':
                print(el['name'],'is dynamic')
                form_links[url][f['method']].append(el['name'])
    return form_links


def get_output_position(links):
    '''
    Get the output position
    '''
    plinks = dict()
    for murl,item in links.items():
        for method,params in item.items():
            for p in params:
                if not murl in plinks:
                    plinks[murl] = dict()
                if not method in plinks[murl]:
                    plinks[murl][method] = dict()
                rnd = ''.join(random.sample(string.ascii_letters,8))
                if method == 'get':
                    response = requests.get(murl,params={p:rnd})
                else:
                    response = requests.post(murl,data={p:rnd})
                regex_rnd = r'.*{0}.*'.format(rnd)
                regex_tags = r'\<.*\>.*?{0}.*?\<\/.*\>'.format(rnd)
                regex_attrs = r'\<.*\=\"{0}\".*\>'.format(rnd)
                regex_js = r'var\s.*?\=.*?\"{0}\";'.format(rnd)
                position = re.findall(regex_rnd,response.text)
                for pos in position:
                    if re.findall(regex_tags,pos):
                        if not 'tags' in plinks[murl][method]:
                            plinks[murl][method]['tags'] = list()
                        print(p,'output on the tags')
                        plinks[murl][method]['tags'].append(p)
                    elif re.findall(regex_attrs,pos):
                        if not 'attrs' in plinks[murl][method]:
                            plinks[murl][method]['attrs'] = list()
                        print(p,'output on the attrs')
                        plinks[murl][method]['attrs'].append(p)
                    elif re.findall(regex_js,pos):
                        if not 'js' in plinks[murl][method]:
                            plinks[murl][method]['js'] = list()
                        print(p,'output on the js')
                        plinks[murl][method]['js'].append(p)
                    else:
                        if not 'page' in plinks[murl][method]:
                            plinks[murl][method]['page'] = list()
                        print(p,'output on the page')
                        plinks[murl][method]['page'].append(p)
    return plinks


def inject_xss_payload(links):
    '''
    Testing XSS vul
    '''
    for murl,mitem in links.items():
        for method,item in mitem.items():
            for pos,params in item.items():
                for p in params:
                    rnd = ''.join(random.sample(string.ascii_letters,8))
                    regex_tagname = r'(?<=\<)(.*)?(?=\>{0})'.format(rnd)
                    if pos == 'tags':
                        if method == 'get':
                            response = requests.get(murl,params={p:rnd})
                        else:
                            response = requests.post(murl,data={p:rnd})
                        tagname = re.findall(regex_tagname,response.text)
                        for tag in tagname:
                            payload = '</{0}><script>alert(/xss/)</script>'.format(tag)
                            if method == 'get':
                                response = requests.get(murl, params={p:payload})
                            else:
                                response = requests.post(murl,data={p:payload})
                            if response.text.find(payload) != -1:
                                print(p,'detect xss:',payload)
                    elif pos == 'attrs':
                        rnd = ''.join(random.sample(string.ascii_letters,8))
                    elif pos == 'js':
                        rnd = ''.join(random.sample(string.ascii_letters,8))
                    else:
                        rnd = ''.join(random.sample(string.ascii_letters,8))


ulinks = get_dynamic_links_url(url)
flinks = get_dynamic_links_form(url)
#rlinks = get_dynamic_links_rest(url)
plinks1 = get_output_position(ulinks)
plinks2 = get_output_position(flinks)
#plinks3 = get_output_position(rlinks)
inject_xss_payload(plinks1)
