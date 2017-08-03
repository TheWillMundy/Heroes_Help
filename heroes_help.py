from flask import Flask, render_template
from flask_ask import Ask, statement, question, session
from fuzzywuzzy import fuzz, process
import json
import requests
import time
import unidecode

app = Flask(__name__)
ask = Ask(app, "/heroes_help")

@app.route('/')
def homepage():
    return 'Greetings, this is an Alexa Skill for Heroes of the Storm. Now shoo, let the Alexa users have their turn.'

@ask.launch
def start_skill():
    welcome_message = "<speak>Hi, welcome to Heroes Helper!</speak>"
    return question(welcome_message)

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
