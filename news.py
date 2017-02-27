import re
import json
from urllib.parse import unquote
from bs4 import BeautifulSoup
import sys
import requests

# -*- coding: UTF-8 -*-
URL_List = []
ARTICLES = dict({})
ID = 0

def run(url):
    parse_urls(get_soup(url))

def parse_urls(soup):
    """ Searches for all links on Google News Search Page """

    for a in soup.find_all('a', href=True):
        link = a['href']

        if "support.google.com/websearch/answer/86640" in link:
            print("IP Address has been blocked by Google")
            sys.exit(0)

        if "/url?q=" in link:
            link = format_link(link)
            if handle_article(link) is 0:
                continue

    del URL_List[:]

def handle_article(link):
    """ Gets Article HTML from Link """
    if link not in URL_List:
        URL_List.append(link)
        val = get_article_page(link)
        if val is not 0:
            global ID
            ID += 1
        return val

def format_link(link):
    """ Sanitizes Link """
    link = link.replace("/url?q=", "", 1)
    idx = link.find("&sa=U&ved")
    link_new = link[:idx]
    #decode uri so requests gets correct html page
    link_new = unquote(unquote(link_new))

    #Will display full article on one page
    if ".reuters." in link_new:
        link_new += "?sp=true"

    return link_new

def get_soup(link):
    """Gets html from link and returns a BS4 Object"""
    try:
        html = requests.get(link).content
    except requests.exceptions.Timeout:
        print("Request for "+ link + " Timed Out")
        return 0
    except requests.exceptions.HTTPError:
        print("Page for link doesn't exist")
    except requests.exceptions.ConnectionError as e:

        return 0

    soup = BeautifulSoup(html.decode('utf-8', 'ignore'), 'html.parser')
    return soup

def get_article_page(link):
    """ Extracts information from Article """
    soup1 = get_soup(link)
    if soup1 is 0:
        return 0
    title = get_title(soup1)
    contents = get_content(soup1)

    global ID

    article = {
        'title': title,
        'link': link,
        'content': contents
    }

    #Adds article dict to our dict of articles
    global ARTICLES
    ARTICLES[ID] = article
    print("Link #"+ str(ID) + " Done\n")
    articles_to_json()

def get_content(soup1):
    """ Retrieves contents of the article """
    content = ""
    #heuristics
    div_tags = soup1.find_all("div", id="articleContentBody")
    div_tags2 = soup1.find_all("div", class_="ArticleText")
    div_tags = soup1.find_all("div", id="ArticleText")
    div3 = soup1.find_all("div", id="article_content")
    div4 = soup1.find_all("div", class_="articleBodyText")
    div5 = soup1.find_all("div", class_="story-container")
    div6 = soup1.find_all("div", class_="kizi-honbun")
    div7 = soup1.find_all("div", class_="main-text")
    rest = soup1.find_all(id="articleText")
    div_tags_l = soup1.find_all("div", id=re.compile("article"))

    if div_tags:
        return collect_content(div_tags)
    elif div_tags2:
        return collect_content(div_tags2)
    elif div_tags:
        return collect_content(div_tags)
    elif div3:
        return collect_content(div3)
    elif div4:
        return collect_content(div4)
    elif div5:
        return collect_content(div5)
    elif div_tags_l:
        return collect_content(div_tags_l)
    elif div6:
        return collect_content(div6)
    elif div7:
        return collect_content(div7)
    elif rest:
        return collect_content(rest)
    else:
        # contingency
        p_tags = soup1.find_all("p")
        for p in p_tags:
            content = content + p.text + '\n'
    return content

def collect_content(parent_tag):
    """ Collects all text from children p tags of parent_tag """
    content = ""
    for tag in parent_tag:
        p_tags = tag.find_all("p")
        for tag in p_tags:
            content += tag.text + '\n'
    return content

def get_title(soup1):
    """ Retrieves Title of Article """
    # Heuristics
    div_tags = soup1.find_all("div", class_="Title")
    article_headline_tags = soup1.find_all("h1", class_="article-headline")
    headline_tags = soup1.find_all("h2", id="main_title")
    hl = soup1.find_all(class_="Title")
    all_h1_tags = soup1.find_all("h1")
    title_match = soup1.find_all(class_=re.compile("title"))
    Title_match = soup1.find_all(class_=re.compile("Title"))
    headline_match = soup1.find_all(class_=re.compile("headline"))

    item_prop_hl = soup1.find_all(itemprop="headline")
    if item_prop_hl:
        return item_prop_hl[0].text

    if div_tags:
        for tag in div_tags:
            h1Tag = tag.find_all("h1")
            for tag in h1Tag:
                if tag.text:
                    return tag.text

    elif article_headline_tags:
        for tag in article_headline_tags:
            return tag.text
    elif headline_tags:
        for tag in headline_tags:
            return tag.text
    elif headline_match:
        return headline_match[0].text
    elif all_h1_tags:
        return all_h1_tags[0].text
    elif hl:
        return hl[0].text
    else:
        if title_match:
            return title_match[0].text
        elif Title_match:
            return Title_match[0].text
        else:
            return ""

def articles_to_json():
    """ Writes articles dictionary into a json file"""
    global ARTICLES
    with open('data.json', 'w', encoding='utf-8') as outfile:
        json.dump(ARTICLES, outfile, ensure_ascii=False, sort_keys=True, indent=4)

def start_scrape():
    """ Begins Scraping of URLs """
    # urls =[
    #     "https://www.google.co.jp/search?cf=all&hl=ja&pz=1&ned=jp&tbm=nws&gl=jp&as_occt=any&as_qdr=a&as_nloc=Japan&authuser=0&start=",
    #     "https://www.google.co.jp/search?q=location:Japan&lr=lang_ja&hl=ja&gl=jp&authuser=0&noj=1&tbs=lr:lang_1ja,qdr:y&tbm=nws&ei=6DGzWPSHCeWEgAa70alI&sa=N&start=",
    #     "https://www.google.co.jp/search?q=location:Japan&hl=ja&gl=jp&authuser=0&noj=1&tbs=qdr:h&tbm=nws&ei=Ny-zWIfeN5OvgAbF2Y-wDQ&sa=N&start=",
    #     "https://www.google.co.jp/search?q=location:Japan&hl=ja&gl=jp&authuser=0&tbs=qdr:d&tbm=nws&sa=N&ech=1&ei=Fi2zWJS6CuWUgAbulYjoDg&emsg=NCSR&noj=1&start="
    #     ]

    # max_start = [990, 990, 40, 80]
    # for url in urls:
        # url_no = 0
    url = "https://www.google.co.jp/search?cf=all&hl=ja&pz=1&ned=jp&tbm=nws&gl=jp&as_occt=any&as_qdr=a&as_nloc=Japan&authuser=0&start="
    for number in range(0,990,10):
        run(url+str(number))
        # url_no += 1
    print("Done!")

start_scrape()
