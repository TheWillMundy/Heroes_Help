from flask import Flask, render_template
from flask_ask import Ask, statement, question, session
from bs4 import BeautifulSoup
from word2number import w2n
from fuzzywuzzy import process
import json
import requests
import time
import unidecode
import inflect
import urllib3
import re
inflect_engine = inflect.engine()
http = urllib3.PoolManager()

app = Flask(__name__)
ask = Ask(app, "/heroes_help")

#Helper Methods
#Tierlist Methods
def get_tierlist(tier):
    url = "https://www.heroescounters.com/tierlist"
    response = requests.get(url)
    html = response.content
    soup = BeautifulSoup(html, "html.parser")
    soup = soup.find(class_="counters-tab-tierlist-currentpatch")
    allHeroes = {}
    for el in soup.findChildren():
        if el.name == 'h2':
            currentTier = unidecode.unidecode(el.contents[0].string)
            allHeroes[currentTier] = []
        elif el.name == 'a':
            hero_name = el['data-heroname'].encode("ascii", "ignore")
            if (hero_name == "Lcio"):
                hero_name = "Lucio"
            allHeroes[currentTier].append(hero_name)
    #allHeroes stores heroes in each tier through dictionary
    return sort_tierlist(tier, allHeroes)

def sort_tierlist(tier, allHeroes):
    if str(tier) == "1":
        return allHeroes['Tier 1 ']
    elif str(tier) == "2":
        return allHeroes['Tier 2 ']
    elif str(tier) == "3":
        return allHeroes['Tier 3 ']
    elif str(tier) == "4":
        return allHeroes['Tier 4 ']
    elif str(tier) == "5":
        return allHeroes['Tier 5 ']
    else:
        allTiers = []
        for tier in sorted(allHeroes):
            allTiers.append(allHeroes[tier])
        return allTiers

def tiername_fixer(tier):
    if tier:
        if (tier == "?"):
            return "all"
        return tier
    return "Something went wrong. Please try again!"

#Best Maps for Heroes
def best_maps(hero_name):
    hero_name = hero_name.lower()
    hero_name = hero_name.replace(" ", "")
    url = "https://www.heroescounters.com/hero/{}#maps".format(hero_name)
    response = requests.get(url)
    html = response.content
    soup = BeautifulSoup(html, "html.parser")
    soup = soup.find(class_="counters-tab-hero-mapranking")
    soup = soup.find(class_="filter-last")
    soup = soup.find(class_="maplist")
    all_maps = []
    for listEl in soup.find_all('li'):
        mapbox = listEl.find(class_="map-box")
        titleTag = mapbox.find('h3')
        map_name = titleTag.find('a').string
        all_maps.append(map_name)
    return all_maps

def getting_heroes():
    url = "https://www.heroescounters.com/"
    html = http.request("GET", url)
    soup = BeautifulSoup(html.data, "html5lib")
    soup = soup.find(class_="home-heroes-list")
    heroes = []
    for row in soup.find_all(class_="home-heroes-list-row"):
        for hero in row.find_all('a'):
            heroes.append(hero["data-heroname"])
    return heroes

def hero_fixer(hero_name):
    allHeroes = getting_heroes()
    allHeroes = set(allHeroes)
    if (re.search(r'the\s', hero_name)):
        hero_name = hero_name.replace("the", "", 1).strip()
    if hero_name.lower() not in map((lambda name: name.lower()), allHeroes):
        matched_hero = process.extractOne(hero_name, allHeroes)
        return matched_hero[0]
    return hero_name.capitalize()

#Best Heroes on each Map
def best_heroes(map_name):
    # map_name = map_name.replace(" ", "")
    map_name = re.sub("\W", "", map_name)
    print map_name
    url = "https://www.heroescounters.com/map/{}".format(map_name)
    html = http.request("GET", url)
    soup = BeautifulSoup(html.data, "html5lib")
    soup = soup.find(class_="counterlist")
    heroes = []
    for listEl in soup.find_all('li'):
        try:
            heroes.append(listEl.div.h3.a.string)
        except:
            pass
    return heroes

def get_all_maps():
    url = "https://www.heroescounters.com/map"
    html = http.request("GET", url)
    soup = BeautifulSoup(html.data, "html5lib")
    soup = soup.find(class_="maplist")
    maps = []
    for map in soup.find_all('li'):
        maps.append(map.a.h3.string)
    return maps

def map_fixer(map_name):
    allMaps = get_all_maps()
    matched_map = process.extractOne(map_name, allMaps)
    return matched_map[0]

@app.route('/')
def homepage():
    return 'Greetings, this is an Alexa Skill for Heroes of the Storm. Now shoo, let the Alexa users have their turn.'

@ask.launch
def start_skill():
    welcome_message = "<speak>Hi, welcome to Heroes Helper!</speak>"
    return question(welcome_message)

@ask.intent("TierIntent", mapping={'tier': 'tier_number'}, default={'tier': 'all'})
def tierlist_intent(tier):
    print "The tier they requested is {}".format(tier)
    #Takes a tier as the slot, returns top heroes in tier (by role)
    tier = str(tier)
    tier = tiername_fixer(tier)
    if (isinstance(tier, basestring) and tier.find("Something") >= 0):
        return statement(tier)
    elif ((tier != "all") and (int(tier) >= 6 or int(tier) <= 0)):
        return statement("<speak> Currently, there are no heroes in this tier. </speak>")
    heroes_list = get_tierlist(tier)
    if (tier != "all" and heroes_list):
        heroes = '<break time="400ms"/>#'.join(heroes_list).split("#")
        heroes = inflect_engine.join(heroes)
        response = '<speak> The heroes in tier {} are <break time="0.5s"/> {} </speak>'.format(tier, heroes)
        return statement(response)
    elif (tier != "all" and not heroes_list):
        response = "<speak> Currently, there are no heroes in this tier. </speak>"
        return statement(response)
    else:
        response = "<speak> "
        for tier_list in heroes_list:
            if tier_list:
                heroes = '<break time="400ms"/>#'.join(tier_list).split("#")
                heroes = inflect_engine.join(heroes)
                response += (' The heroes in tier {} are <break time="0.5s"/> {} <break time="0.75s"/>'.format(heroes_list.index(tier_list) + 1, heroes))
            else:
                response += (' There are no heroes in tier {}. '.format(heroes_list.index(tier_list) + 1))
        response += (" </speak>")
        return statement(response)

@ask.intent("MapIntent")
def map_intent(hero_name):
    hero_name = hero_fixer(hero_name) #Need to create
    maps = best_maps(hero_name)
    mapped_names = ""
    for map_index in range(0,3):
        mapped_names += '{} <break time="0.3s"/>#'.format(maps[map_index])
    mapped_names = mapped_names.split("#")
    mapped_names.pop()
    print mapped_names
    mapped_names = inflect_engine.join(mapped_names)
    response = render_template("map_msg", hero_name=hero_name, maps=mapped_names)
    return statement(response)

@ask.intent("HeroMapIntent", default={'map_name': 'Battlefield of Eternity', 'hero_num': 6})
def hero_map_intent(map_name, hero_num):
    if hero_num is "?":
        hero_num = 6
    map_name = map_fixer(map_name)
    heroes = best_heroes(map_name)
    hero_names = ""
    for hero_index in range(0, int(hero_num)):
        hero_names += '{} <break time="0.3s"/>#'.format(heroes[hero_index])
    hero_names = hero_names.split("#")
    hero_names.pop()
    hero_names = inflect_engine.join(hero_names)
    response = render_template("hero_map_msg", hero_num=hero_num, map_name=map_name, heroes=hero_names)
    return statement(response)

@ask.intent("AMAZON.HelpIntent")
def help_intent():
    help_text = '<speak></speak>'
    return question(help_text)

@ask.intent("AMAZON.CancelIntent")
def cancel_intent():
    print("User canceled the interaction")
    return statement('')

@ask.intent("AMAZON.StopIntent")
def stop_intent():
    print("User canceled the interaction")
    return statement('')

if __name__ == '__main__':
    app.run(debug=False)
