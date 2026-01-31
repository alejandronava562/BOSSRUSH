from __future__ import annotations

import base64
import json
import os
import random
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY) if API_KEY else None

app = Flask(__name__)


@dataclass
class Player:
    hp: int
    turn: int = 1
    shield: int = 0        # Reduces incoming damage
    attack_bonus: int = 0  # Extra damage dealt to bosses
    max_hp: int = 7        # Track max HP for healing rewards


@dataclass
class Boss:
    name: str
    category: str
    hp: int
    image_data_url: Optional[str] = None


SYSTEM = (
    "You are a boss fight narrator that teaches sustainability. "
    "Keep language appropriate for kids and families."
)

BOSS_LIBRARY: List[Tuple[str, str]] = [
    ("The Landfill Lord", "incompetence or destructiveness in environmental stewardship"),
    ("Carbon King", "carbon footprint, pollution, global warming"),
    ("Mr. Incinerator", "waste burning, pollution"),
    ("Tree Slayer", "deforestation and habitat destruction"),
    ("Plastic Pirate", "plastic pollution in rivers and oceans"),
    ("Water Waster", "water pollution and wasting clean water"),
    ("Energy Eater", "wasting electricity and fossil fuel dependence"),
    ("Air Polluter", "air pollution and emissions"),
    ("Soil Spoiler", "soil contamination and degradation"),
    ("Wildlife Wrecker", "biodiversity loss and habitat destruction"),
    ("Ocean Obliterator", "marine pollution and overfishing"),
    ("Climate Conqueror", "climate change and global warming"),
    ("Garbage Goblin", "waste management and littering"),
    ("Fossil Fuel Fiend", "fossil fuel dependence and pollution"),
    ("Chemical Crusher", "chemical pollution and hazardous waste"),
    ("Noise Nemesis", "noise pollution and disturbance"),
    ("Light Looter", "light pollution and energy waste"),
    ("Forest Fumbler", "destroying habitats and ecosystems"),
    ("Chief Habitat Wrecker", "destroying habitats"),
]


def _difficulty_settings(difficulty: str) -> Dict[str, Any]:
    hp_by_difficulty = {"easy": 10, "medium": 7, "hard": 5}
    boss_hp_by_difficulty = {"easy": 35, "medium": 45, "hard": 55}
    required_wins = {"easy": 3, "medium": 5, "hard": 7}
    sustainable_choices = {"easy": 2, "medium": 1, "hard": 1}

    return {
        "player_hp": hp_by_difficulty.get(difficulty, 7),
        "boss_hp": boss_hp_by_difficulty.get(difficulty, 45),
        "required_wins": required_wins.get(difficulty, 5),
        "sustainable_choices": sustainable_choices.get(difficulty, 1),
    }


STATE: Dict[str, Any] = {
    "active": False,
    "username": None,
    "difficulty": None,
    "required_wins": 0,
    "wins": 0,
    "current_boss_index": 0,
    "player": Player(hp=7),
    "bosses": [],  # list[Boss as dict]
    "current_scene_raw": None,  # stores full model payload including deltas
    "log": [],
}

# Pre-fetch queue for background scene generation (keeps multiple scenes ready)
_prefetch_lock = threading.Lock()
_prefetch_queue: Deque[Dict[str, Any]] = deque()  # Queue of {"boss_index": int, ...scene_data}
_prefetch_target = 3  # Keep this many scenes ready in the queue
_prefetch_running = False  # Prevents multiple prefetch threads from running


def _extract_json_object(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model did not return JSON.")
    return json.loads(text[start : end + 1])


def _clamp_int(value: Any, min_value: int, max_value: int) -> int:
    try:
        n = int(value)
    except Exception:
        n = 0
    return max(min_value, min(max_value, n))


def _validate_and_normalize_scene(
    payload: Dict[str, Any], sustainable_needed: int
) -> Dict[str, Any]:
    scene = str(payload.get("scene", "")).strip()
    choices = payload.get("choices", [])
    if not scene or not isinstance(choices, list) or len(choices) != 4:
        raise ValueError("Invalid scene payload.")

    normalized: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    for choice in choices:
        cid = str(choice.get("id", "")).strip().upper()
        if cid not in {"A", "B", "C", "D"} or cid in seen_ids:
            raise ValueError("Choices must have unique ids A-D.")
        seen_ids.add(cid)

        text = str(choice.get("text", "")).strip()
        if not text:
            raise ValueError("Choice text is required.")

        is_sustainable = bool(choice.get("is_sustainable", False))
        delta_player = choice.get("delta_player", {}) or {}
        delta_boss = choice.get("delta_boss", {}) or {}

        dp = _clamp_int(delta_player.get("hp", 0), -10, 2)
        db = _clamp_int(delta_boss.get("hp", 0), -20, 5)

        normalized.append(
            {
                "id": cid,
                "text": text,
                "is_sustainable": is_sustainable,
                "delta_player": {"hp": dp},
                "delta_boss": {"hp": db},
            }
        )

    sustainable_count = sum(1 for c in normalized if c["is_sustainable"])
    if sustainable_count != sustainable_needed:
        raise ValueError("Wrong number of sustainable choices.")

    return {"scene": scene, "choices": normalized}


def _fallback_scene(boss: Boss, player: Player, sustainable_needed: int) -> Dict[str, Any]:
    scene = (
        f"{boss.name} blocks your path and brags about {boss.category}. "
        "You remember that small choices can protect the planet. "
        "What do you do?"
    )

    sustainable = [
        {
            "id": "A",
            "text": "Refuse the wasteful plan and choose a reuse/repair option instead.",
            "is_sustainable": True,
            "delta_player": {"hp": 0},
            "delta_boss": {"hp": -12},
        },
        {
            "id": "B",
            "text": "Pick a low-carbon option (save energy, avoid single-use, and recycle right).",
            "is_sustainable": True,
            "delta_player": {"hp": 1},
            "delta_boss": {"hp": -10},
        },
    ]
    unsustainable = [
        {
            "id": "C",
            "text": "Do the easy-but-wasteful option and throw everything away.",
            "is_sustainable": False,
            "delta_player": {"hp": -4},
            "delta_boss": {"hp": -2},
        },
        {
            "id": "D",
            "text": "Ignore the impact and use extra resources just to be faster.",
            "is_sustainable": False,
            "delta_player": {"hp": -5},
            "delta_boss": {"hp": 0},
        },
    ]

    if sustainable_needed == 1:
        sustainable = [sustainable[0]]
        unsustainable = [
            {**unsustainable[0], "id": "B"},
            {**unsustainable[1], "id": "C"},
            {
                "id": "D",
                "text": "Use more power and water than you need, because it feels strong.",
                "is_sustainable": False,
                "delta_player": {"hp": -6},
                "delta_boss": {"hp": -1},
            },
        ]

    choices = (sustainable + unsustainable)[:4]
    return {"scene": scene, "choices": choices}


def build_scene_prompt(boss: Boss, player: Player, difficulty: str) -> str:
    sustainable_needed = _difficulty_settings(difficulty)["sustainable_choices"]
    return f"""
Boss Name: {boss.name}
Boss Category: {boss.category}
Difficulty: {difficulty}

Current Stats:
- Player HP: {player.hp}
- Boss HP: {boss.hp}

Write a new battle scene (3-5 sentences) with 4 choices (A-D).

Rules:
- Exactly {sustainable_needed} out of 4 choices must be sustainable (good for the environment).
- The other choices must be unsustainable (wasteful, polluting, or harmful).
- Do not label which choices are correct in the scene text.
- Keep language kid-friendly.
- Each choice must include:
  - id: "A" | "B" | "C" | "D"
  - text: short, clear action
  - is_sustainable: boolean
  - delta_player.hp: int (range -10 to 2)
  - delta_boss.hp: int (range -20 to 5)

Balancing:
- Sustainable choices should usually be better for the player and deal more damage to the boss.
- Unsustainable choices should usually hurt the player and deal little/no damage to the boss.

Return JSON only in this exact shape:
{{
  "scene": "string",
  "choices": [
    {{
      "id": "A",
      "text": "string",
      "is_sustainable": true,
      "delta_player": {{"hp": 0}},
      "delta_boss": {{"hp": -12}}
    }}
  ]
}}
""".strip()


def _ask_model_for_scene(boss: Boss, player: Player, difficulty: str) -> Dict[str, Any]:
    if not client:
        return _fallback_scene(boss, player, _difficulty_settings(difficulty)["sustainable_choices"])

    prompt = build_scene_prompt(boss, player, difficulty)
    sustainable_needed = _difficulty_settings(difficulty)["sustainable_choices"]

    last_error: Optional[Exception] = None
    for attempt in range(3):
        try:
            response = client.responses.create(
                model="gpt-5-mini",
                input=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            )
            data = _extract_json_object(response.output_text)
            return _validate_and_normalize_scene(data, sustainable_needed)
        except Exception as e:
            last_error = e
            time.sleep(0.6 * (attempt + 1))

    # Last-resort fallback so the app remains playable.
    return _fallback_scene(boss, player, sustainable_needed)


def _scene_for_client(scene_raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "scene": scene_raw["scene"],
        "choices": [{"id": c["id"], "text": c["text"]} for c in scene_raw["choices"]],
    }


def _prefetch_worker() -> None:
    """Background worker that keeps the prefetch queue filled with scenes."""
    global _prefetch_running

    with _prefetch_lock:
        if _prefetch_running:
            return  # Another worker is already running
        _prefetch_running = True

    try:
        while True:
            # Check if we should stop
            if not STATE.get("active"):
                break

            # Check queue size
            with _prefetch_lock:
                queue_size = len(_prefetch_queue)
                if queue_size >= _prefetch_target:
                    break  # Queue is full

            # Generate a new scene
            boss_index = STATE["current_boss_index"]
            boss_dict = STATE["bosses"][boss_index]
            boss = Boss(**{k: boss_dict[k] for k in ["name", "category", "hp"]})
            difficulty = STATE["difficulty"]

            try:
                scene = _ask_model_for_scene(boss, STATE["player"], difficulty)
                with _prefetch_lock:
                    # Double-check boss hasn't changed while we were generating
                    if STATE["current_boss_index"] == boss_index:
                        _prefetch_queue.append({"boss_index": boss_index, **scene})
            except Exception:
                # Failed to generate - stop trying to avoid infinite loop on errors
                break
    finally:
        with _prefetch_lock:
            _prefetch_running = False


def _start_prefetch() -> None:
    """Kick off background pre-fetch worker to fill the queue."""
    threading.Thread(target=_prefetch_worker, daemon=True).start()


def _get_prefetched_scene(boss_index: int) -> Optional[Dict[str, Any]]:
    """Get a pre-fetched scene from the queue if available and matches current boss."""
    with _prefetch_lock:
        # Find and remove the first scene that matches this boss
        for i, scene in enumerate(_prefetch_queue):
            if scene.get("boss_index") == boss_index:
                del _prefetch_queue[i]
                return scene
        return None


def _clear_prefetch() -> None:
    """Clear the prefetch queue (e.g., on boss transition)."""
    with _prefetch_lock:
        _prefetch_queue.clear()


def _get_queue_size() -> int:
    """Get current number of scenes in the prefetch queue (for debugging)."""
    with _prefetch_lock:
        return len(_prefetch_queue)


def _boss_image_placeholder(boss: Boss) -> str:
    initials = "".join([w[0] for w in boss.name.split()[:2]]).upper() or "B"
    svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0ea5e9"/>
      <stop offset="1" stop-color="#22c55e"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="36" fill="url(#g)"/>
  <text x="50%" y="52%" text-anchor="middle" font-size="168" font-family="system-ui,Segoe UI,Roboto" fill="#052e16" font-weight="800">
    {initials}
  </text>
</svg>
""".strip()
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def _boss_name_to_filename(name: str) -> str:
    """Convert boss name to a safe filename: 'Ocean Obliterator' -> 'ocean_obliterator'"""
    return name.lower().replace(" ", "_").replace("-", "_")


def _check_custom_boss_image(boss_name: str) -> Optional[str]:
    filename_base = _boss_name_to_filename(boss_name)
    extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]
    
    for ext in extensions:
        filepath = os.path.join("static", "boss_images", filename_base + ext)
        if os.path.exists(filepath):
            # Return URL path for the static file
            return f"/static/boss_images/{filename_base}{ext}"
    
    return None


def _get_boss_image(boss_dict: Dict[str, Any]) -> str:
    """Get boss image from custom uploads, with placeholder fallback."""
    # Return cached image if available
    if boss_dict.get("image_data_url"):
        return boss_dict["image_data_url"]
    
    # Check for custom student-uploaded image
    custom_image = _check_custom_boss_image(boss_dict.get("name", ""))
    if custom_image:
        boss_dict["image_data_url"] = custom_image
        return custom_image
    
    # Fallback to placeholder if no custom image
    boss = Boss(**{k: boss_dict.get(k) for k in ["name", "category", "hp"]})
    boss_dict["image_data_url"] = _boss_image_placeholder(boss)
    return boss_dict["image_data_url"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/start", methods=["GET", "POST"])
def start_game():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip() or "Player"
    difficulty = (payload.get("difficulty") or "").strip().lower()
    if difficulty not in {"easy", "medium", "hard"}:
        return jsonify({"error": "Difficulty must be easy, medium, or hard."}), 400

    settings = _difficulty_settings(difficulty)

    bosses = []
    for name, category in BOSS_LIBRARY:
        bosses.append(Boss(name=name, category=category, hp=settings["boss_hp"]).__dict__)
    random.shuffle(bosses)

    STATE.update(
        {
            "active": True,
            "username": username,
            "difficulty": difficulty,
            "required_wins": settings["required_wins"],
            "wins": 0,
            "current_boss_index": 0,
            "player": Player(hp=settings["player_hp"], max_hp=settings["player_hp"]),
            "bosses": bosses,
            "current_scene_raw": None,
            "pending_reward": False,  # True when player needs to choose a reward
            "log": [],
        }
    )

    # Clear any stale prefetch from previous game and start filling queue immediately
    # This runs IN PARALLEL with first scene generation below, so by the time
    # the loading screen finishes, we may already have 2-3 scenes queued up
    _clear_prefetch()
    _start_prefetch()

    # Pre-load first boss scene and image so the UI feels instant.
    boss_dict = STATE["bosses"][STATE["current_boss_index"]]
    boss = Boss(**{k: boss_dict[k] for k in ["name", "category", "hp"]})
    scene_raw = _ask_model_for_scene(boss, STATE["player"], difficulty)
    STATE["current_scene_raw"] = {"boss_index": STATE["current_boss_index"], **scene_raw}

    image_data_url = _get_boss_image(boss_dict)

    return jsonify(
        {
            "message": "Game started.",
            "username": username,
            "difficulty": difficulty,
            "required_wins": STATE["required_wins"],
            "wins": STATE["wins"],
            "current_boss_index": STATE["current_boss_index"],
            "player_hp": STATE["player"].hp,
            "player_max_hp": STATE["player"].max_hp,
            "player_shield": STATE["player"].shield,
            "player_attack_bonus": STATE["player"].attack_bonus,
            "boss": {"name": boss_dict["name"], "category": boss_dict["category"], "hp": boss_dict["hp"]},
            "boss_image": image_data_url,
            **_scene_for_client(scene_raw),
        }
    )


def _get_player_stats() -> Dict[str, Any]:
    """Helper to get current player stats for API responses."""
    return {
        "player_hp": STATE["player"].hp,
        "player_max_hp": STATE["player"].max_hp,
        "player_shield": STATE["player"].shield,
        "player_attack_bonus": STATE["player"].attack_bonus,
    }


def _get_reward_options() -> List[Dict[str, Any]]:
    """Generate the three reward options for defeating a boss."""
    return [
        {
            "id": "shield",
            "name": "Shield Boost",
            "description": "+1 Shield (reduces damage taken)",
            "icon": "🛡️",
        },
        {
            "id": "health",
            "name": "Health Restore",
            "description": f"Restore 3 HP (max {STATE['player'].max_hp})",
            "icon": "❤️",
        },
        {
            "id": "attack",
            "name": "Attack Power",
            "description": "+2 Attack (deal more damage to bosses)",
            "icon": "⚔️",
        },
        {
            "id": "Food",
            "name": "Crispy Noodles",
            "description": "Plus 25 percent attack Plus 25% Deffense Plus 25% Special Deffense Plus 25% Special Attack, Unlock way of Eco Heaven",
            "icon": "🍜",
        },
        {
            "id": "Armor",
            "name": "Everbloom Aegis",
            "description": "Takes 50 percent less damage ",
            "icon": "🥻",
        },
        {
            "id": "Magic/Spell",
            "name": "Gateway Of Living Grace",
            "description": "Instant kill with force field for 3 blows ",
            "icon": "🪄",
        },
    ]


@app.route("/api/scene", methods=["POST"])
def scene():
    if not STATE.get("active"):
        return jsonify({"error": "Game not started."}), 400

    data = request.get_json(silent=True) or {}
    boss_index = int(data.get("boss_index", STATE["current_boss_index"]))
    boss_index = max(0, min(boss_index, len(STATE["bosses"]) - 1))
    STATE["current_boss_index"] = boss_index

    boss_dict = STATE["bosses"][boss_index]
    boss = Boss(**{k: boss_dict[k] for k in ["name", "category", "hp"]})
    difficulty = STATE["difficulty"]

    scene_raw = _ask_model_for_scene(boss, STATE["player"], difficulty)
    STATE["current_scene_raw"] = {"boss_index": boss_index, **scene_raw}

    image_data_url = _get_boss_image(boss_dict)

    # Start pre-fetching next scene in background
    _start_prefetch()

    return jsonify(
        {
            "username": STATE["username"],
            "difficulty": difficulty,
            "required_wins": STATE["required_wins"],
            "wins": STATE["wins"],
            "current_boss_index": boss_index,
            "boss": {"name": boss_dict["name"], "category": boss_dict["category"], "hp": boss_dict["hp"]},
            "boss_image": image_data_url,
            **_get_player_stats(),
            **_scene_for_client(scene_raw),
        }
    )

@app.route("/api/apply_choice", methods=["POST"])
def apply_choice():
    if not STATE.get("active"):
        return jsonify({"error": "Game not started."}), 400
    
    if STATE.get("pending_reward"):
        return jsonify({"error": "Please claim your reward first!"}), 400

    data = request.get_json(silent=True) or {}
    choice_id = str(data.get("choice_id", "")).strip().upper()
    if choice_id not in {"A", "B", "C", "D"}:
        return jsonify({"error": "choice_id must be A, B, C, or D."}), 400

    boss_index = STATE["current_boss_index"]
    boss_dict = STATE["bosses"][boss_index]
    boss = Boss(**{k: boss_dict[k] for k in ["name", "category", "hp"]})
    difficulty = STATE["difficulty"]

    scene_raw = STATE.get("current_scene_raw")
    if not scene_raw or scene_raw.get("boss_index") != boss_index:
        scene_raw = _ask_model_for_scene(boss, STATE["player"], difficulty)
        scene_raw = {"boss_index": boss_index, **scene_raw}
        STATE["current_scene_raw"] = scene_raw

    selected = next((c for c in scene_raw["choices"] if c["id"] == choice_id), None)
    if not selected:
        return jsonify({"error": "Choice not found."}), 400

    dp = int(selected["delta_player"]["hp"])
    db = int(selected["delta_boss"]["hp"])
    was_sustainable = bool(selected["is_sustainable"])

    # Apply shield: reduces incoming damage (if dp is negative, shield makes it less negative)
    if dp < 0:
        dp = min(0, dp + STATE["player"].shield)  # Shield can't make damage positive
    
    # Apply attack bonus: increases damage dealt to boss (make db more negative)
    if db < 0:
        db = db - STATE["player"].attack_bonus  # More negative = more damage

    STATE["player"].hp += dp
    boss_dict["hp"] += db
    STATE["player"].hp = max(0, min(STATE["player"].hp, STATE["player"].max_hp))  # Clamp to max
    boss_dict["hp"] = max(0, boss_dict["hp"])

    if STATE["player"].hp <= 0:
        STATE["active"] = False
        return jsonify(
            {
                "outcome": "player_defeated",
                "message": "You ran out of HP. Try again and pick more sustainable choices!",
                "was_sustainable": was_sustainable,
                "boss": {"name": boss_dict["name"], "category": boss_dict["category"], "hp": boss_dict["hp"]},
                **_get_player_stats(),
            }
        )

    if boss_dict["hp"] <= 0:
        STATE["wins"] += 1
        if STATE["wins"] >= STATE["required_wins"]:
            STATE["active"] = False
            return jsonify(
                {
                    "outcome": "victory",
                    "message": "Victory! You defeated all the bosses with sustainable choices!",
                    "was_sustainable": was_sustainable,
                    "wins": STATE["wins"],
                    "required_wins": STATE["required_wins"],
                    **_get_player_stats(),
                }
            )

        # Boss defeated but more to go - offer reward choice!
        STATE["pending_reward"] = True
        
        return jsonify(
            {
                "outcome": "boss_defeated_choose_reward",
                "message": f"You defeated {boss_dict['name']}! Choose your reward:",
                "was_sustainable": was_sustainable,
                "wins": STATE["wins"],
                "required_wins": STATE["required_wins"],
                "rewards": _get_reward_options(),
                **_get_player_stats(),
            }
        )

    # Continue same boss - try to use pre-fetched scene for instant response
    boss = Boss(**{k: boss_dict[k] for k in ["name", "category", "hp"]})
    next_scene_raw = _get_prefetched_scene(boss_index)
    if not next_scene_raw:
        # Fallback to sync generation if prefetch not ready
        next_scene_raw = _ask_model_for_scene(boss, STATE["player"], difficulty)
        next_scene_raw = {"boss_index": boss_index, **next_scene_raw}
    STATE["current_scene_raw"] = next_scene_raw
    
    # Reuse cached image - boss hasn't changed, no need to re-fetch
    image_data_url = boss_dict.get("image_data_url") or _get_boss_image(boss_dict)

    # Start pre-fetching next scene in background
    _start_prefetch()

    return jsonify(
        {
            "outcome": "continue",
            "message": "Nice choice!" if was_sustainable else "Ouch—try a more sustainable option next time!",
            "was_sustainable": was_sustainable,
            "wins": STATE["wins"],
            "required_wins": STATE["required_wins"],
            "current_boss_index": boss_index,
            "boss": {"name": boss_dict["name"], "category": boss_dict["category"], "hp": boss_dict["hp"]},
            "boss_image": image_data_url,
            **_get_player_stats(),
            **_scene_for_client(next_scene_raw),
        }
    )


@app.route("/api/claim_reward", methods=["POST"])
def claim_reward():
    """Player claims their reward after defeating a boss."""
    if not STATE.get("active"):
        return jsonify({"error": "Game not started."}), 400
    
    if not STATE.get("pending_reward"):
        return jsonify({"error": "No reward pending."}), 400

    data = request.get_json(silent=True) or {}
    reward_id = str(data.get("reward_id", "")).strip().lower()
    
    if reward_id not in {"shield", "health", "attack"}:
        return jsonify({"error": "Invalid reward. Choose shield, health, or attack."}), 400

    # Apply the chosen reward
    reward_message = ""
    if reward_id == "shield":
        STATE["player"].shield += 1
        reward_message = f"Shield increased to {STATE['player'].shield}! You now take less damage."
    elif reward_id == "health":
        old_hp = STATE["player"].hp
        STATE["player"].hp = min(STATE["player"].hp + 3, STATE["player"].max_hp)
        healed = STATE["player"].hp - old_hp
        reward_message = f"Restored {healed} HP! (Now at {STATE['player'].hp}/{STATE['player'].max_hp})"
    elif reward_id == "attack":
        STATE["player"].attack_bonus += 2
        reward_message = f"Attack power increased to +{STATE['player'].attack_bonus}! You now deal more damage."

    # Clear pending reward
    STATE["pending_reward"] = False

    # Now advance to next boss
    _clear_prefetch()
    
    STATE["current_boss_index"] = min(STATE["current_boss_index"] + 1, len(STATE["bosses"]) - 1)
    next_boss_dict = STATE["bosses"][STATE["current_boss_index"]]
    next_boss = Boss(**{k: next_boss_dict[k] for k in ["name", "category", "hp"]})
    difficulty = STATE["difficulty"]
    
    next_scene_raw = _ask_model_for_scene(next_boss, STATE["player"], difficulty)
    STATE["current_scene_raw"] = {"boss_index": STATE["current_boss_index"], **next_scene_raw}
    image_data_url = _get_boss_image(next_boss_dict)

    # Start pre-fetching for the new boss
    _start_prefetch()

    return jsonify(
        {
            "outcome": "reward_claimed",
            "reward_id": reward_id,
            "reward_message": reward_message,
            "message": f"A new challenger appears: {next_boss_dict['name']}!",
            "wins": STATE["wins"],
            "required_wins": STATE["required_wins"],
            "current_boss_index": STATE["current_boss_index"],
            "boss": {
                "name": next_boss_dict["name"],
                "category": next_boss_dict["category"],
                "hp": next_boss_dict["hp"],
            },
            "boss_image": image_data_url,
            **_get_player_stats(),
            **_scene_for_client(next_scene_raw),
        }
    )


@app.route("/api/boss_image", methods=["POST"])
def boss_image():
    if not STATE.get("active"):
        return jsonify({"error": "Game not started."}), 400

    data = request.get_json(silent=True) or {}
    boss_index = int(data.get("boss_index", STATE["current_boss_index"]))
    boss_index = max(0, min(boss_index, len(STATE["bosses"]) - 1))
    boss_dict = STATE["bosses"][boss_index]
    return jsonify({"boss_image": _get_boss_image(boss_dict)})


@app.route("/api/boss_list", methods=["GET"])
def boss_list():
    """
    Returns all bosses with their expected image filenames.
    Useful for students to know what to name their Sora-generated images!
    
    Visit: http://localhost:5000/api/boss_list
    """
    bosses = []
    for name, category in BOSS_LIBRARY:
        filename = _boss_name_to_filename(name)
        has_custom = _check_custom_boss_image(name) is not None
        bosses.append({
            "name": name,
            "category": category,
            "filename": filename,
            "example": f"{filename}.png",
            "has_custom_image": has_custom,
        })
    return jsonify({"bosses": bosses})

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
    if not client:
        return jsonify(
            {
                "fact": "Did you know? Turning off the tap while brushing your teeth can save a lot of water each day!"
            }
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": user_prompt},
                {"role": "system", "content": system_prompt},
            ],
        )
        return jsonify({"fact": response.choices[0].message.content})
    except Exception:
        return jsonify(
            {
                "fact": "Quick tip: Reuse what you can, recycle what you should, and reduce what you use!"
            }
        )

if __name__ == "__main__":
    app.run(debug=True)
