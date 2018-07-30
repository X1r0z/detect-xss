from urllib.parse import urlsplit,urljoin
from bs4 import BeautifulSoup as bs
import requests
import random
import string
import re

url = 'http://127.0.0.1/xss-example/';

def get_dynamic_links_url(murl):
    '''
    Read dynamic links from url, only GET
    
    result:
        {'http://127.0.0.1/xss.php': ['id', 'form', 'callback', 'protect1', 'protect2']}
    '''
    url_links = dict() 
    response = requests.get(murl)
    html = bs(response.text,'html.parser')
    a = html.find_all(name='a')
    for el in a:
        parse = urlsplit(el['href'])
        query = parse[3]
            ''''
            1. adasd.php
            2. /a/safasf/asd.php
            3. http://www.adasd.com/adfsad.php
            4. //www.asdsad.com/adsasd.php

            '''
        if query
            print(el['href'],'is dynamic')
            if not url in url_links:
                url_links[url] = list()
            name = query.split('=',1)[0]
            url_links[url].append(name)
    return url_links


def get_dynamic_links_rest(murl):
    '''
    Read dynamic links from REST url, only GET
    '''
    pass


def get_dynamic_links_form(murl):
    '''
    Read dynmaic links from form, GET and POST

    result:
        {'http://127.0.0.1/xss.php': {'get': ['form', 'protect2'], 'post': ['user', 'pass', 'code']}}
    '''
    form_links = dict()
    response = requests.get(murl)
    html = bs(response.text,'html.parser')
    form = html.find_all(name='form')
    for f in form:
        parse = urlsplit(f['action'])
        query = parse[3]
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


def get_output_position(ulinks):
    '''
    {'http://127.0.0.1/xss.php': ['id', 'form', 'callback', 'protect1', 'protect2']}
    '''
    '''
    {'http://127.0.0.1/xss.php': {'get': ['form', 'protect2'], 'post': ['user', 'pass', 'code']}}
    '''
    for murl,params in ulinks.items():
        for p in params:
            rnd = ''.join(random.sample(string.ascii_letters,8))
            response  = requests.get(murl,params={p:rnd})
            regex_rnd = r'(.*)?STRING(.*)?'
            regex_tags = r'\<.((?!script).)*\>.*?STRING.*?\<\/((?!script).)*\>'
            regex_attrs = r'\<.*?\=\".*?STRING.*?\"\>.*?<\/.*?\>'
            regex_js = r'\<script\>.*?STRING.*?<\/script\>'
            position = re.findall(regex_rnd,response.text)
            for pos in position:
                if pos == rnd:
                    print('output on the page')


ulinks = get_dynamic_links_url(url)
flinks = get_dynamic_links_form(url)
print(ulinks)
print(flinks)