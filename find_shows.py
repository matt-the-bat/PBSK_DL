#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Shows on Tue Mar 11th 2025:
    
almas-way
arthur
brambletown
carl-the-collector
city-island
clifford-the-big-red-dog
curious-george
cyberchase
daniel-tigers-neighborhood
design-squad
dinosaur-train
donkey-hodie
elinor-wonders-why
hero-elementary
jamming-on-the-job
jelly-ben-pogo
keyshawn-solves-it
lets-go-luna
lyla-in-the-loop
martha-speaks
maya-miguel
mecha-builders
milo
mister-rogers-neighborhood
molly-of-denali
nature-cat
odd-squad
oh-noah
pbs-kids-mega-wow
pbs-kids-talk-about
peg-cat
pinkalicious-and-peterrific
plum-landing
ready-jet-go
rocket-saves-the-day
rosies-rules
scigirls
scribbles-and-ink
search-it-up
sesame-street
sid-the-science-kid
skillsville
splash-and-bubbles
super-why
super-whys-comic-book-adventures
team-hamster-ruff-ruffman
the-cat-in-the-hat-knows-a-lot-about-that
through-the-woods
tiny-time-travel
together-we-can
what-can-you-become
wild-kratts
word-world
wordgirl
work-it-out-wombats
xavier-riddle-and-the-secret-museum

"""
import urllib
from bs4 import BeautifulSoup


def run():
    ''' Open the website to look for videos '''
    URLROOT = "https://pbskids.org/videos"
    MAGICSTRING = 'PropertiesNavigationBanner_emblaSlide__7kbWK'
    show_names = []

    with urllib.request.urlopen(URLROOT) as html:
        # suppose 'html' is your HTML content
        soup = BeautifulSoup(html.read(), 'html.parser')
        # find all <li> elements with class
        lis = soup.find_all('li', class_=MAGICSTRING)
        # loop through each <li> element and find the <a> tag inside it
        for li in lis:
            a_tag = li.find('a')
            if a_tag:
                href = a_tag.get('href')
            show_names.append(href[8:])  # append the href value
    for _ in sorted(show_names):
        print(_)


if __name__ == "__main__":
    run()
