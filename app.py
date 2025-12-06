from flask import Flask, request, jsonify
import json, random, time, os
from dataclasses import dataclass, asdict
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
# === Imported code from boss_rush.py (unchanged except I removed input() loops) === #
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

@dataclass
class BOBBY:
    hp: int = 25
    turn: int = 1

@dataclass
class Robert:
    name: str
    category: str
    hp: int = 50

STATE: Dict[str, Any] = {
    "player": BOBBY(),
    "bosses": [
        Robert(name="The Landfill Lord", category="incompetence or destructiveness in environmental stewardship").__dict__,
        Robert(name="Carbon King", category="carbon footprint, pollution, global warming").__dict__,
        Robert(name="Mr. Incinerator", category="waste burning,  pollution").__dict__,
    ],
    "log": []
}

SYSTEM = (
    "You are a boss fight narrator that teaches sustainability. "
    "Keep language appropriate for kids and families."
)

def build_scene_prompt(boss: Robert, player: BOBBY) -> str:
    return f"""
    Boss Name: {boss.name}
    Boss Category: {boss.category}

    Current Stats:
    - Player HP: {player.hp}
    - Boss HP: {boss.hp}

    Write a new battle scene with 4 choices.
    Return JSON only:
    {{
        "scene": "...",
        "choices": [
            {{
                "id": "A",
                "text": "choice text",
                "delta_player": {{"hp": -5}},
                "delta_boss": {{"hp": -5}}
            }}
        ]
    }}
    """

def ask_model(boss, player):
    prompt = build_scene_prompt(boss, player)
    response = client.responses.create(
        model="gpt-5-mini",
        input=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt} 
        ],
    )
    return json.loads(response.output_text)


# === Flask App === #

app = Flask(__name__)

@app.route("/api/start", methods=["GET"])
def start_game():
    random.shuffle(STATE["bosses"])
    STATE["player"] = BOBBY()
    return jsonify({"message": "Game started.", "bosses": STATE["bosses"]})

@app.route("/api/scene", methods=["POST"])
def scene():
    data = request.json
    boss_index = data["boss_index"]

    boss = Robert(**STATE["bosses"][boss_index])
    player = STATE["player"]

    result = ask_model(boss, player)
    return jsonify(result)

@app.route("/api/apply_choice", methods=["POST"])
def apply_choice():
    data = request.json
    boss_index = data["boss_index"]
    delta_player = data["delta_player"]
    delta_boss = data["delta_boss"]

    STATE["player"].hp += delta_player["hp"]
    STATE["bosses"][boss_index]["hp"] += delta_boss["hp"]

    return jsonify({
        "player_hp": STATE["player"].hp,
        "boss_hp": STATE["bosses"][boss_index]["hp"]
    })

# === ask_questions.py adapted === #
@app.route("/api/questions", methods=["POST"])
def daily_questions():
    d = request.json
    answers = {
        "Method Travel": d.get("bike_or_car"),
        "Water running": d.get("water_running"),
        "Touch_Grass_Minutes": d.get("touch_grass"),
        "Routes": d.get("route")
    }
    return jsonify(answers)

# === facts.py adapted === #
@app.route("/api/fact", methods=["GET"])
def fact():
    user_prompt = "Give me random fact about sustainability."
    system_prompt = """
    Generate a random fact about touching grass time, water consumption,
    transportation choices, or carbon footprint.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": user_prompt},
            {"role": "system", "content": system_prompt}
        ]
    )

    return jsonify({"fact": response.choices[0].message.content})

if __name__ == "__main__":
    app.run(debug=True)
