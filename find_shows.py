#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 10 12:55:48 2025

"""
import urllib
from bs4 import BeautifulSoup

urlroot = "https://pbskids.org/videos"
show_names = []

with urllib.request.urlopen(urlroot) as html:
    # suppose 'html' is your HTML content
    soup = BeautifulSoup(html.read(), 'html.parser')
    # find all <li> elements with class "PropertiesNavigationBanner_emblaSlide__7kbWK
    lis = soup.find_all('li', class_='PropertiesNavigationBanner_emblaSlide__7kbWK')
    # loop through each <li> element and find the <a> tag inside it
    for li in lis:
        a_tag = li.find('a')
        if a_tag: href = a_tag.get('href')
        show_names.append(href[8:]) # append the href value
for _ in sorted(show_names):
    print(_)