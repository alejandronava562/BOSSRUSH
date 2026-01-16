from flask import Flask, request, jsonify, render_template, Response
import json, random, time, os, re
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
    hp: int = 3
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
    "log": [],
    "prefetched_scenes": {} 
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

    Write a battle scene about environmental sustainability related to the boss's category.
    
    IMPORTANT: Create exactly 4 choices where:
    - ONE choice is clearly the CORRECT sustainable/eco-friendly answer (deals -10 to -15 damage to boss, 0 damage to player)
    - THREE choices are clearly WRONG or harmful to the environment (deal -1 to -4 damage to player, 0 damage to boss)
    
    Make it obvious which answer teaches good sustainability practices.
    
    Return JSON only:
    {{
        "scene": "2-3 sentence battle scene describing the environmental challenge",
        "choices": [
            {{
                "id": "A",
                "text": "choice text",
                "delta_player": {{"hp": 0 or negative int}},
                "delta_boss": {{"hp": 0 or negative int}}
            }},
            {{
                "id": "B",
                "text": "choice text", 
                "delta_player": {{"hp": 0 or negative int}},
                "delta_boss": {{"hp": 0 or negative int}}
            }},
            {{
                "id": "C",
                "text": "choice text",
                "delta_player": {{"hp": 0 or negative int}},
                "delta_boss": {{"hp": 0 or negative int}}
            }},
            {{
                "id": "D",
                "text": "choice text",
                "delta_player": {{"hp": 0 or negative int}},
                "delta_boss": {{"hp": 0 or negative int}}
            }}
        ]
    }}
    """

def shuffle_choices(data):
    """Shuffle choices and reassign IDs A, B, C, D."""
    if "choices" in data and len(data["choices"]) > 1:
        random.shuffle(data["choices"])
        for i, choice in enumerate(data["choices"]):
            choice["id"] = chr(65 + i)  # A, B, C, D
    return data

def ask_model(boss, player):
    prompt = build_scene_prompt(boss, player)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt} 
        ],
    )
    try:
        result = json.loads(response.choices[0].message.content)
        return shuffle_choices(result)
    except (json.JSONDecodeError, IndexError, AttributeError) as e:
        return {
            "scene": "An error occurred generating the scene. Please try again.",
            "choices": [{"id": "A", "text": "Retry", "delta_player": {"hp": 0}, "delta_boss": {"hp": 0}}]
        }

def stream_scene(boss, player):
    """Generator that yields SSE events for streaming scene text."""
    prompt = build_scene_prompt(boss, player)
    
    try:
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        
        full_response = ""
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                # Yield each chunk as SSE event
                yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"
        
        # Parse the full response and send final data
        try:
            # Clean JSON from markdown code blocks if present
            cleaned = re.sub(r'^```json\s*', '', full_response.strip())
            cleaned = re.sub(r'\s*```$', '', cleaned)
            parsed = json.loads(cleaned)
            shuffled = shuffle_choices(parsed)
            yield f"data: {json.dumps({'type': 'complete', 'scene': shuffled.get('scene', ''), 'choices': shuffled.get('choices', [])})}\n\n"
        except json.JSONDecodeError:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to parse response'})}\n\n"
            
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


# === Flask App === #

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/start", methods=["GET", "POST"])
def start_game():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username")
    difficulty = payload.get("difficulty")
    hp_by_difficulty = {"easy": 20, "medium": 15, "hard": 10}
    if not difficulty:
        return jsonify({"error": "Missing difficulty"}), 400
    
    start_hp = hp_by_difficulty.get(difficulty, 3)
    random.shuffle(STATE["bosses"])
    STATE["player"] = BOBBY(hp=start_hp)
    STATE["username"] = username
    STATE["difficulty"] = difficulty

    return jsonify({
        "message": "Game started.",
        "bosses": STATE["bosses"],
        "username": username,
        "difficulty": difficulty,
        "player_hp": STATE["player"].hp
    })

@app.route("/api/scene", methods=["POST"])
def scene():
    data = request.json
    boss_index = data["boss_index"]
    
    cache_key = f"boss_{boss_index}_hp_{STATE['bosses'][boss_index]['hp']}_player_{STATE['player'].hp}"
    if cache_key in STATE["prefetched_scenes"]:
        result = STATE["prefetched_scenes"].pop(cache_key)
        return jsonify(result)

    boss = Robert(**STATE["bosses"][boss_index])
    player = STATE["player"]

    result = ask_model(boss, player)
    return jsonify(result)

@app.route("/api/scene/stream", methods=["POST"])
def scene_stream():
    """Stream scene text via SSE for typewriter effect."""
    data = request.json
    boss_index = data["boss_index"]
    
    # Check cache first - if cached, return as single complete event
    cache_key = f"boss_{boss_index}_hp_{STATE['bosses'][boss_index]['hp']}_player_{STATE['player'].hp}"
    if cache_key in STATE["prefetched_scenes"]:
        result = STATE["prefetched_scenes"].pop(cache_key)
        def cached_response():
            yield f"data: {json.dumps({'type': 'complete', 'scene': result.get('scene', ''), 'choices': result.get('choices', [])})}\n\n"
        return Response(cached_response(), mimetype='text/event-stream')
    
    boss = Robert(**STATE["bosses"][boss_index])
    player = STATE["player"]
    
    return Response(stream_scene(boss, player), mimetype='text/event-stream')

@app.route("/api/apply_choice", methods=["POST"])
def apply_choice():
    data = request.json
    boss_index = data["boss_index"]
    delta_player = data["delta_player"]
    delta_boss = data["delta_boss"]

    STATE["player"].hp += delta_player["hp"]
    STATE["bosses"][boss_index]["hp"] += delta_boss["hp"]
    
    try:
        if STATE["bosses"][boss_index]["hp"] > 0 and STATE["player"].hp > 0:
            boss = Robert(**STATE["bosses"][boss_index])
            player = STATE["player"]
            next_scene = ask_model(boss, player)
            cache_key = f"boss_{boss_index}_hp_{boss.hp}_player_{player.hp}"
            STATE["prefetched_scenes"][cache_key] = next_scene
    except Exception:
        pass  # Silent fail—scene will be generated on-demand if prefetch fails

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
@app.route("/api/fact", methods=["POST"])
def fact():
    data = request.json or {}
    topic = data.get("topic", "sustainability")
    
    user_prompt = f"Give me a short, interesting fact about {topic}."
    system_prompt = """
    You are an environmental educator. Generate a single, concise sentence (max 20 words) 
    that teaches a specific fact about the given topic. 
    Focus on impact and actionable knowledge.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=60
        )
        return jsonify({"fact": response.choices[0].message.content})
    except Exception:
        # Fallback if API fails
        return jsonify({"fact": "Did you know? Recycling one aluminum can saves enough energy to run a TV for three hours."})

if __name__ == "__main__":
    app.run(debug=True)
