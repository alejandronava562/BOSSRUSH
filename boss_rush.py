import os, json, time, sys, random
from dotenv import load_dotenv
load_dotenv()  # loads environment variables from .env
from dataclasses import dataclass, asdict
from typing import Dict, Any, List
from openai import OpenAI

# ---- comment here ---- #
# Alejandro
#Lucas
# Harry
# Eason
# Eddy
# ---------------------- #

# ---- app name here ---- #

# ---------------------- #

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
        Robert(name = "The Landfill Lord", category = "").__dict__,
        Robert(name = "Carbon King", category = "carbon footprint, pollution, global warming").__dict__,
        Robert(name = "Mr. Incinerator", category = "waste burning,  pollution").__dict__,
        Robert(name = "The Lorax Jr", category = "Habitats and Ecosystem").__dict__,
        Robert(name = "Tree Slayer", category = "Tree cutter").__dict__, 
        Robert(name = "Plastic Pirate", category = "Plastic pollution").__dict__,
        Robert(name = "Water Waster", category = "Water pollution and wastage").__dict__,
        Robert(name = "Energy Eater", category = "Energy consumption and wastage").__dict__,
        Robert(name = "Air Polluter", category = "Air pollution and emissions").__dict__,
        Robert(name = "Soil Spoiler", category = "Soil contamination and degradation").__dict__,
        Robert(name = "Wildlife Wrecker", category = "Biodiversity loss and habitat destruction").__dict__,
        Robert(name = "Ocean Obliterator", category = "Marine pollution and overfishing").__dict__,
        Robert(name = "Climate Conqueror", category = "Climate change and global warming").__dict__,
        Robert(name = "Garbage Goblin", category = "Waste management and littering").__dict__,
        Robert(name = "Fossil Fuel Fiend", category = "Fossil fuel dependence and pollution").__dict__,
        Robert(name = "Chemical Crusher", category = "Chemical pollution and hazardous waste").__dict__,
        Robert(name = "Noise Nemesis", category = "Noise pollution and disturbance").__dict__,
        Robert(name = "Light Looter", category = "Light pollution and energy waste").__dict__,
    ],
    "log": []
}

# =============================== #
# ---------- Prompting ---------- #
# =============================== #
SYSTEM = (
    ""
)

def build_scene_prompt(boss: Robert, player: BOBBY) -> str:
    SCENE_PROMPT = f"""
    Boss Name: {boss.name}
    Boss Category: {boss.category}

    Current Stats:
    - Player HP: {player.hp}
    - Boss HP: {boss.hp}

    Stats:
    - Player delta keys: hp
    - Boss delta keys: hp

    Write a new battle scene that fits the boss topic and
    Scene Rules:
    - 3 to 5 sentences
    - Offer 4 choices

    Return a strict JSON only. Template:
    {{
        "choices" : [
        {{
            "id: "A",
            "text" : "choice text",
            "delta_player": {"hp": "int in range (-10, 0)"}
            "delta_boss": {"hp": "int in range (-10, 0)"}
        }},
        {{
            "id: "B",
            "text" : "choice text",
            "delta_player": {"hp": "int in range (-10, 0)"}
            "delta_boss": {"hp": "int in range (-10, 0)"}
        }},
        {{
            "id: "C",
            "text" : "choice text",
            "delta_player": {"hp": "int in range (-10, 0)"}
            "delta_boss": {"hp": "int in range (-10, 0)"}
        }},
        {{
            "id: "D",
            "text" : "choice text",
            "delta_player": {"hp": "int in range (-10, 0)"}
            "delta_boss": {"hp": "int in range (-10, 0)"}
        }},
        ]
    }}
    
    """
    return SCENE_PROMPT
    


print("Welcome to the eco-sustainible Boss Rush Game, in this game you will fight bosses that aren't eco-sustainible, and by answering sustainible questions right, you can damage the bosses.Good Luck!") 
print(" Welcome to the bike-travelling Boss Escape Game, in this game you will run around and avoid the smashing car on a bike! You can escape! Good Luck!")