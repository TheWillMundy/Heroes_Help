from flask import Flask, render_template
from flask_ask import Ask, statement, question, session
from bs4 import BeautifulSoup
from word2number import w2n
import json
import requests
import time
import unidecode
import inflect
inflect_engine = inflect.engine()

app = Flask(__name__)
ask = Ask(app, "/heroes_help")

#Helper Methods
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
        if (tier.isalnum() and tier.lower() == "all"):
            return tier
        return w2n.word_to_num(tier)
    return "Something went wrong. Please try again!"

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
