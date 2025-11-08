import os, json, time, sys, random
from dotenv import load_dotenv
load_dotenv()  # loads environment variables from .env
from dataclasses import dataclass, asdict
from typing import Dict, Any, List
from openai import OpenAI


API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)
# ----- Game State ----- #
@dataclass
class BOBBY:
    hp: int = 25
    turn: int = 1

@dataclass
# (Enviromental sustainability hater1)
# The Landfill Lord - name
# Mr Lorax Jr - name
# Carbon King/Queen - name
# Mr. Incinerator - name
class Robert:   
    name: str
    category: str
    hp: int = 50


STATE: Dict[str, Any] = {
    "player": BOBBY(),
    "bosses" : [
        Robert(name = "The Landfill Lord", category = "landfills, trash").__dict__,
        Robert(name = "Carbon King", category = "carbon footprint, pollution, global warming").__dict__,
        Robert(name = "Mr. Incinerator", category = "waste burning,  pollution").__dict__,
        Robert(name = "The Lorax Jr", category = "Tree cutter").__dict__
    ]
}

print("Welcome to the eco-sustainible Boss Rush Game, in this game you will fight bosses that aren't eco-sustainible, and by answering sustainible questions right, you can damage the bosses.Good Luck!") 
print(" Welcome to the bike-travelling Boss Escape Game, in this game you will run around and avoid the smashing car on a bike! You can escape! Good Luck!")
    