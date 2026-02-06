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
    shield: int = 0              # Reduces incoming damage (20% per level)
    attack_bonus: int = 0        # Extra damage dealt to bosses
    max_hp: int = 7              # Track max HP for healing rewards
    critical_strike_chance: int = 0  # 10% per level for bonus damage
    force_field_turns: int = 0   # Remaining turns of force field active (50% damage reduction)
    eco_blaster_uses: int = 0    # Charges of Eco Blaster (removes wrong answer)
    aegis_active: bool = False   # Everbloom Aegis permanent 50% damage reduction
    # Activatable item charges (held in inventory, player chooses when to use)
    noodles_charges: int = 0     # Organic Crispy Noodles charges
    aegis_charges: int = 0       # Everbloom Aegis charges
    spell_charges: int = 0       # Gateway Of Living Grace charges


@dataclass
class Boss:
    name: str
    category: str
    hp: int
    image_data_url: Optional[str] = None


SYSTEM = (
    "You are an engaging environmental educator who creates fun boss battles "
    "that teach kids about sustainability, recycling, composting, energy conservation, "
    "water conservation, and reducing waste. "
    "Make each choice action-oriented, concrete, and kid-friendly. "
    "Each choice should teach a different sustainability practice. "
    "IMPORTANT: Vary your writing style, tone, and scenarios every time. "
    "Use different verbs, settings, and storytelling angles. Never repeat the same scene structure."
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
_prefetch_target = 8  # Keep 8 scenes ready (seamless multi-choice gameplay)
_prefetch_running = False  # Prevents multiple prefetch threads from running

# Scene history tracking to avoid repetitive questions
_scene_history: Deque[str] = deque(maxlen=30)  # Track last 30 scene texts
_choice_history: Deque[str] = deque(maxlen=60)  # Track last 60 choice texts

# Cache for boss image filesystem lookups (boss_name -> url or None)
_boss_image_cache: Dict[str, Optional[str]] = {}


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

        dp = _clamp_int(delta_player.get("hp", 0), -10, 0)
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


# === CATEGORIZED QUESTION BANKS FOR VARIETY ===

_SCENE_TEMPLATES: Dict[str, List[str]] = {
    "confrontation": [
        "{boss} towers before you, smog billowing from its shoulders. The ground cracks beneath its toxic footsteps. You must act fast—every second counts!",
        "{boss} roars with fury, sending shockwaves of pollution across the land. Nearby animals flee in terror. What will you do to fight back?",
        "{boss} has set up a fortress of waste and destruction. It dares you to try and stop the damage. Your next move could change everything!",
        "The sky darkens as {boss} unleashes a wave of environmental chaos. Trees wilt and rivers turn murky. Time to make a difference!",
        "{boss} cackles as garbage piles grow higher around you. The stench is unbearable! You spot several ways to turn the tide.",
    ],
    "discovery": [
        "You stumble upon {boss}'s secret lair—a wasteland of {category}. Hidden among the wreckage, you see clues about how to weaken this villain.",
        "Deep in {boss}'s territory, you discover the source of {category}. Knowledge is power—what strategy will you use?",
        "A mysterious map leads you to where {boss} draws its power from {category}. You have one chance to strike at the root of the problem!",
        "Your eco-scanner reveals {boss}'s weakness: it feeds on {category}. If you cut off its supply, victory is yours!",
        "An ancient tree spirit whispers the secret to defeating {boss}—it's all connected to {category}. Choose wisely!",
    ],
    "rescue": [
        "Villagers cry for help as {boss} spreads {category} across their home. They look to you for guidance. What's your plan?",
        "A group of endangered animals is trapped by {boss}'s {category} attack! You must rescue them and weaken the boss at the same time.",
        "The local river is poisoned by {boss}'s power over {category}. The fish are gasping! Your choice will determine their fate.",
        "{boss} has captured the town's clean water supply using {category}. Townspeople are counting on you to break free!",
        "A school playground is under siege from {boss}'s {category} rampage! The kids need a hero. What will you do?",
    ],
    "puzzle": [
        "{boss} has placed a riddle before you: solve the sustainability puzzle or face the consequences of {category}. Think carefully!",
        "To unlock {boss}'s cage of {category}, you must demonstrate true eco-knowledge. Which action proves you're a sustainability champion?",
        "{boss} laughs and says: 'Only someone who truly understands {category} can defeat me!' Prove them wrong!",
        "A magical barrier powered by {category} blocks your path. {boss} watches smugly. Only the right eco-action will break through!",
        "{boss} challenges you to an eco-duel! Whoever makes the most sustainable choice about {category} wins the round!",
    ],
    "race": [
        "Time is running out! {boss} is about to unleash a massive {category} disaster. You have seconds to choose your counter-attack!",
        "{boss} has started a countdown—when it hits zero, {category} will overwhelm the city. Quick, what's your move?",
        "The eco-alarm blares! {boss} is accelerating {category} faster than ever. Every moment you hesitate, the planet suffers more!",
        "A tidal wave of {category} is headed straight for the coast, powered by {boss}. You spot four possible responses—choose NOW!",
        "{boss} has rigged a pollution bomb tied to {category}! Only the right sustainable action can defuse it in time!",
    ],
}

_SUSTAINABLE_BANK: Dict[str, List[Dict[str, Any]]] = {
    "recycling": [
        {"text": "Sort recyclables into correct bins.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -12}},
        {"text": "Recycle old electronics at a drop-off.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Rinse containers before recycling them.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Flatten cardboard boxes for recycling.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Start a neighborhood recycling drive.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -12}},
        {"text": "Return glass bottles to be reused.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
    ],
    "reusing": [
        {"text": "Repair the broken item instead.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Donate old clothes to a thrift store.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Use a reusable water bottle daily.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Repurpose glass jars for storage.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Mend torn clothing instead of tossing.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Swap books with friends, don't buy new.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -12}},
    ],
    "composting": [
        {"text": "Compost the food scraps.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Start a worm bin for composting.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Add yard waste to compost pile.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Use compost to grow a garden.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -12}},
        {"text": "Compost coffee grounds and eggshells.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Set up a school composting station.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
    ],
    "energy": [
        {"text": "Turn off lights when leaving a room.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -9}},
        {"text": "Switch to LED light bulbs.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Unplug chargers when not in use.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Use a solar-powered phone charger.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -12}},
        {"text": "Hang clothes to dry instead of dryer.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Open curtains for natural light.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Set thermostat two degrees lower.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Use a power strip to save standby energy.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
    ],
    "water": [
        {"text": "Close the tap while brushing teeth.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Take shorter showers to save water.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Collect rainwater for the garden.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -12}},
        {"text": "Fix the leaky faucet right away.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Water plants in the cool morning.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Use a bucket, not a hose, to wash.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Install a low-flow showerhead.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -12}},
    ],
    "transport": [
        {"text": "Bike or walk instead of driving.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -9}},
        {"text": "Take the bus or carpool to school.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Ride a scooter for short errands.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Use public transit for long trips.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Walk to nearby stores instead of driving.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Organize a walking school bus.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -12}},
    ],
    "reducing": [
        {"text": "Bring reusable bags to the store.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Say no to single-use plastic straws.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Buy in bulk to reduce packaging.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -12}},
        {"text": "Choose products with less packaging.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Use a lunchbox instead of plastic bags.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Borrow tools instead of buying new.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Use cloth napkins instead of paper.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
    ],
    "nature": [
        {"text": "Plant a tree in the community.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -12}},
        {"text": "Build a bird feeder from scraps.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Start a pollinator-friendly garden.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Pick up litter on a nature walk.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -12}},
        {"text": "Create a wildlife habitat in your yard.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Join a local beach or river cleanup.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
    ],
    "food": [
        {"text": "Eat local, seasonal produce.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Grow your own vegetables at home.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -12}},
        {"text": "Pack a zero-waste lunch.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Choose a meatless meal today.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
        {"text": "Save leftovers instead of wasting food.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -10}},
        {"text": "Shop at a local farmers market.", "delta_player": {"hp": 0}, "delta_boss": {"hp": -11}},
    ],
}

_UNSUSTAINABLE_BANK: Dict[str, List[Dict[str, Any]]] = {
    "waste": [
        {"text": "Throw everything in the trash.", "delta_player": {"hp": -4}, "delta_boss": {"hp": -2}},
        {"text": "Toss recyclables into the garbage.", "delta_player": {"hp": -5}, "delta_boss": {"hp": -1}},
        {"text": "Dump food waste in the landfill.", "delta_player": {"hp": -4}, "delta_boss": {"hp": -1}},
        {"text": "Litter on the ground and walk away.", "delta_player": {"hp": -6}, "delta_boss": {"hp": 0}},
        {"text": "Use a new plastic bag every trip.", "delta_player": {"hp": -4}, "delta_boss": {"hp": -1}},
        {"text": "Throw away clothes after wearing once.", "delta_player": {"hp": -5}, "delta_boss": {"hp": -1}},
    ],
    "consumption": [
        {"text": "Buy a new one instead of fixing.", "delta_player": {"hp": -5}, "delta_boss": {"hp": 0}},
        {"text": "Order stuff you don't really need.", "delta_player": {"hp": -4}, "delta_boss": {"hp": -1}},
        {"text": "Buy products with tons of packaging.", "delta_player": {"hp": -5}, "delta_boss": {"hp": -1}},
        {"text": "Always choose disposable over reusable.", "delta_player": {"hp": -4}, "delta_boss": {"hp": 0}},
        {"text": "Get a new phone every year.", "delta_player": {"hp": -5}, "delta_boss": {"hp": -1}},
        {"text": "Use single-use cups every day.", "delta_player": {"hp": -4}, "delta_boss": {"hp": -1}},
    ],
    "energy_waste": [
        {"text": "Leave the lights on all day.", "delta_player": {"hp": -3}, "delta_boss": {"hp": 0}},
        {"text": "Blast the AC with windows open.", "delta_player": {"hp": -5}, "delta_boss": {"hp": -1}},
        {"text": "Leave electronics plugged in 24/7.", "delta_player": {"hp": -4}, "delta_boss": {"hp": 0}},
        {"text": "Run the dishwasher half-empty.", "delta_player": {"hp": -3}, "delta_boss": {"hp": -1}},
        {"text": "Keep the TV on when nobody's watching.", "delta_player": {"hp": -4}, "delta_boss": {"hp": 0}},
        {"text": "Use the dryer for one shirt.", "delta_player": {"hp": -3}, "delta_boss": {"hp": -1}},
    ],
    "water_waste": [
        {"text": "Leave the tap running nonstop.", "delta_player": {"hp": -6}, "delta_boss": {"hp": -1}},
        {"text": "Take a 30-minute hot shower.", "delta_player": {"hp": -4}, "delta_boss": {"hp": -1}},
        {"text": "Hose down the driveway for fun.", "delta_player": {"hp": -5}, "delta_boss": {"hp": 0}},
        {"text": "Ignore the dripping faucet.", "delta_player": {"hp": -4}, "delta_boss": {"hp": -1}},
        {"text": "Water the lawn in the blazing sun.", "delta_player": {"hp": -5}, "delta_boss": {"hp": 0}},
        {"text": "Pour chemicals down the drain.", "delta_player": {"hp": -6}, "delta_boss": {"hp": -1}},
    ],
    "transport_waste": [
        {"text": "Drive a car for one block.", "delta_player": {"hp": -4}, "delta_boss": {"hp": -1}},
        {"text": "Always drive alone, never carpool.", "delta_player": {"hp": -5}, "delta_boss": {"hp": -1}},
        {"text": "Idle the engine while waiting.", "delta_player": {"hp": -4}, "delta_boss": {"hp": 0}},
        {"text": "Take a plane for a short trip.", "delta_player": {"hp": -5}, "delta_boss": {"hp": -1}},
        {"text": "Rev the engine for no reason.", "delta_player": {"hp": -4}, "delta_boss": {"hp": 0}},
        {"text": "Refuse to walk even five minutes.", "delta_player": {"hp": -3}, "delta_boss": {"hp": -1}},
    ],
    "nature_harm": [
        {"text": "Cut down trees for no reason.", "delta_player": {"hp": -5}, "delta_boss": {"hp": -1}},
        {"text": "Dump trash in the river.", "delta_player": {"hp": -6}, "delta_boss": {"hp": 0}},
        {"text": "Spray harmful pesticides everywhere.", "delta_player": {"hp": -5}, "delta_boss": {"hp": -1}},
        {"text": "Destroy animal habitats for fun.", "delta_player": {"hp": -6}, "delta_boss": {"hp": 0}},
        {"text": "Release balloons into the sky.", "delta_player": {"hp": -4}, "delta_boss": {"hp": -1}},
        {"text": "Pick wildflowers and trample the trail.", "delta_player": {"hp": -3}, "delta_boss": {"hp": -1}},
    ],
}


def _pick_fresh_choices(
    bank: Dict[str, List[Dict[str, Any]]], count: int, history: Deque[str]
) -> List[Dict[str, Any]]:
    """Pick choices from the categorized bank, avoiding recently used ones."""
    all_choices: List[Dict[str, Any]] = []
    categories = list(bank.keys())
    random.shuffle(categories)
    for cat in categories:
        for item in bank[cat]:
            all_choices.append({**item, "_category": cat})
    random.shuffle(all_choices)

    # Prefer choices not recently seen
    history_set = set(history)
    fresh = [c for c in all_choices if c["text"] not in history_set]
    stale = [c for c in all_choices if c["text"] in history_set]

    # Try to pick from different categories
    picked: List[Dict[str, Any]] = []
    used_cats: set = set()
    for c in fresh:
        if len(picked) >= count:
            break
        if c["_category"] not in used_cats:
            picked.append(c)
            used_cats.add(c["_category"])
    # Fill remaining if needed (relax category constraint)
    for c in fresh + stale:
        if len(picked) >= count:
            break
        if c not in picked:
            picked.append(c)

    # Clean up internal tracking key
    for c in picked:
        c.pop("_category", None)
    return picked[:count]


def _fallback_scene(boss: Boss, player: Player, sustainable_needed: int) -> Dict[str, Any]:
    # Pick a random scene template style
    style = random.choice(list(_SCENE_TEMPLATES.keys()))
    templates = _SCENE_TEMPLATES[style]
    scene = random.choice(templates).format(boss=boss.name, category=boss.category)

    # Pick fresh choices avoiding recently used ones
    sustainable_picks = _pick_fresh_choices(
        _SUSTAINABLE_BANK, sustainable_needed, _choice_history
    )
    unsustainable_picks = _pick_fresh_choices(
        _UNSUSTAINABLE_BANK, 4 - sustainable_needed, _choice_history
    )

    choices = []
    for item in sustainable_picks:
        choices.append({**item, "is_sustainable": True})
    for item in unsustainable_picks:
        choices.append({**item, "is_sustainable": False})

    # SHUFFLE choices to randomize positions (A, B, C, D)
    random.shuffle(choices)

    # Assign IDs after shuffling so correct answers appear in random positions
    for i, choice in enumerate(choices):
        choice["id"] = chr(65 + i)  # A, B, C, D

    # Record to history
    _scene_history.append(scene)
    for c in choices:
        _choice_history.append(c["text"])

    return {"scene": scene, "choices": choices}


def build_scene_prompt(boss: Boss, player: Player, difficulty: str) -> str:
    sustainable_needed = _difficulty_settings(difficulty)["sustainable_choices"]

    # Pick a random narrative style to force variety
    narrative_styles = [
        "Write the scene as an urgent rescue mission.",
        "Write the scene as a mystery discovery.",
        "Write the scene as a tense race against time.",
        "Write the scene as a clever puzzle challenge.",
        "Write the scene as an epic showdown.",
        "Write the scene from a young hero's perspective.",
        "Write the scene set in a school or playground.",
        "Write the scene in a forest or ocean setting.",
        "Write the scene as a neighborhood adventure.",
        "Write the scene as a science experiment gone wrong.",
    ]
    style_instruction = random.choice(narrative_styles)

    # Pick random sustainability topics to force diverse choices
    all_topics = [
        "recycling", "reusing & repairing", "composting", "saving energy",
        "saving water", "biking/walking", "reducing packaging", "planting trees",
        "protecting wildlife", "eating local food", "reducing food waste",
        "avoiding single-use plastic", "using renewable energy", "cleaning up litter",
        "choosing durable products", "public transit", "reducing noise pollution",
        "supporting local farmers", "building habitats", "conserving soil",
    ]
    random.shuffle(all_topics)
    required_topics = all_topics[:4]  # Force 4 different topics

    # Build recent-history exclusion hint
    recent_hints = ""
    if _choice_history:
        recent_samples = list(_choice_history)[-12:]
        recent_hints = (
            "\nDO NOT reuse any of these recent choice texts:\n"
            + "\n".join(f"  - \"{t}\"" for t in recent_samples)
            + "\n"
        )

    return f"""
Boss Name: {boss.name}
Boss Category: {boss.category}
Difficulty: {difficulty}

Current Stats:
- Player HP: {player.hp}
- Boss HP: {boss.hp}

NARRATIVE STYLE: {style_instruction}

Create an engaging battle scene (3-5 sentences) about confronting {boss.name}.
Then provide 4 distinct action choices (A-D), each ONE SENTENCE (max 10 words).

CHOICE TOPICS (you MUST use these 4 specific topics, one per choice):
1. {required_topics[0]}
2. {required_topics[1]}
3. {required_topics[2]}
4. {required_topics[3]}

CHOICE VARIETY RULES:
- EXACTLY {sustainable_needed} choices must be sustainable (eco-friendly).
- The remaining choices must be unsustainable (wasteful/harmful).
- Each of the 4 choices MUST cover its assigned topic above.
- RANDOMIZE the position of sustainable vs unsustainable choices.
- Use DIFFERENT verbs and scenarios than common examples.
{recent_hints}
JSON STRUCTURE (choices A-D must be in this exact format):
{{
  "scene": "A vivid 3-5 sentence battle scene description.",
  "choices": [
    {{
      "id": "A",
      "text": "One specific action about {required_topics[0]} (max 10 words).",
      "is_sustainable": true,
      "delta_player": {{"hp": 0}},
      "delta_boss": {{"hp": -12}}
    }},
    {{
      "id": "B",
      "text": "Different action about {required_topics[1]} (max 10 words).",
      "is_sustainable": false,
      "delta_player": {{"hp": -4}},
      "delta_boss": {{"hp": -1}}
    }},
    {{
      "id": "C",
      "text": "Another action about {required_topics[2]} (max 10 words).",
      "is_sustainable": false,
      "delta_player": {{"hp": -5}},
      "delta_boss": {{"hp": 0}}
    }},
    {{
      "id": "D",
      "text": "Final action about {required_topics[3]} (max 10 words).",
      "is_sustainable": true,
      "delta_player": {{"hp": 0}},
      "delta_boss": {{"hp": -10}}
    }}
  ]
}}

REMINDERS:
- Choice text must be concise (under 10 words).
- Return ONLY valid JSON, no extra text.
- All 4 choices must teach different lessons about their assigned topics.
- RANDOMIZE order: Do NOT put all sustainable choices first or all unsustainable choices last.
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
            scene = _validate_and_normalize_scene(data, sustainable_needed)
            # Record to history to avoid future repeats
            _scene_history.append(scene["scene"])
            for c in scene["choices"]:
                _choice_history.append(c["text"])
            return scene
        except Exception as e:
            last_error = e
            time.sleep(0.3 * (attempt + 1))  # 0.3s, 0.6s, 0.9s — fast retries

    # Last-resort fallback so the app remains playable.
    return _fallback_scene(boss, player, sustainable_needed)


def _scene_for_client(scene_raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "scene": scene_raw["scene"],
        "choices": [{"id": c["id"], "text": c["text"]} for c in scene_raw["choices"]],
    }


def _prefetch_worker() -> None:
    """Aggressive background worker that keeps prefetch queue continuously filled.
    Generates multiple scenes proactively so users experience zero latency.
    """
    global _prefetch_running

    with _prefetch_lock:
        if _prefetch_running:
            return  # Another worker is already running
        _prefetch_running = True

    try:
        consecutive_failures = 0
        while True:
            # Check if we should stop
            if not STATE.get("active"):
                break

            # Check queue size and refill aggressively
            with _prefetch_lock:
                queue_size = len(_prefetch_queue)
                if queue_size >= _prefetch_target:
                    # Queue full - sleep longer to avoid CPU spin
                    time.sleep(0.5)
                    continue

            # Generate a new scene for current boss
            boss_index = STATE["current_boss_index"]
            if boss_index >= len(STATE["bosses"]):
                break
                
            boss_dict = STATE["bosses"][boss_index]
            boss = Boss(**{k: boss_dict[k] for k in ["name", "category", "hp"]})
            difficulty = STATE["difficulty"]

            try:
                scene = _ask_model_for_scene(boss, STATE["player"], difficulty)
                with _prefetch_lock:
                    # Double-check boss hasn't changed while we were generating
                    if STATE["current_boss_index"] == boss_index:
                        _prefetch_queue.append({"boss_index": boss_index, **scene})
                        consecutive_failures = 0  # Reset failure counter on success
            except Exception:
                # Track failures - give up after 2 consecutive failures to avoid spam
                consecutive_failures += 1
                if consecutive_failures >= 2:
                    break  # Stop on persistent failures
                time.sleep(0.5)  # Brief wait before retry
    finally:
        with _prefetch_lock:
            _prefetch_running = False


def _start_prefetch() -> None:
    """Kick off background pre-fetch worker to fill the queue.
    Safe to call multiple times - only one worker runs at a time.
    """
    with _prefetch_lock:
        if not _prefetch_running:  # Only start if not already running
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
    return name.lower().replace(" ", "_").replace("-", "_").replace(".", "")


def _check_custom_boss_image(boss_name: str) -> Optional[str]:
    # Return cached result if available
    if boss_name in _boss_image_cache:
        return _boss_image_cache[boss_name]

    filename_base = _boss_name_to_filename(boss_name)
    extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]
    
    for ext in extensions:
        filepath = os.path.join("static", "boss_images", filename_base + ext)
        if os.path.exists(filepath):
            url = f"/static/boss_images/{filename_base}{ext}"
            _boss_image_cache[boss_name] = url
            return url
    
    _boss_image_cache[boss_name] = None
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
    _clear_prefetch()
    _scene_history.clear()
    _choice_history.clear()

    # Use instant fallback for first scene — AI scenes will fill queue during story
    boss_dict = STATE["bosses"][STATE["current_boss_index"]]
    boss = Boss(**{k: boss_dict[k] for k in ["name", "category", "hp"]})
    scene_raw = _fallback_scene(
        boss, STATE["player"],
        _difficulty_settings(difficulty)["sustainable_choices"]
    )
    STATE["current_scene_raw"] = {"boss_index": STATE["current_boss_index"], **scene_raw}

    # Start prefetch worker — it will fill queue with AI scenes while story plays
    _start_prefetch()

    image_data_url = _get_boss_image(boss_dict)

    return jsonify(
        {
            "message": "Game started.",
            "username": username,
            "difficulty": difficulty,
            "required_wins": STATE["required_wins"],
            "wins": STATE["wins"],
            "current_boss_index": STATE["current_boss_index"],
            "boss": {"name": boss_dict["name"], "category": boss_dict["category"], "hp": boss_dict["hp"]},
            "boss_image": image_data_url,
            **_get_player_stats(),
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
        "player_critical_strike": STATE["player"].critical_strike_chance,
        "player_force_field_turns": STATE["player"].force_field_turns,
        "player_eco_blaster_uses": STATE["player"].eco_blaster_uses,
        "player_aegis_active": STATE["player"].aegis_active,
        "player_noodles_charges": STATE["player"].noodles_charges,
        "player_aegis_charges": STATE["player"].aegis_charges,
        "player_spell_charges": STATE["player"].spell_charges,
    }


def _get_reward_options() -> List[Dict[str, Any]]:
    """Generate 3 random reward options from a pool of 7 for defeating a boss."""
    all_rewards = [
        {
            "id": "shield_boost",
            "name": "Shield Boost",
            "description": "20% less damage (stacks with existing shields)",
            "icon": "🛡️",
        },
        {
            "id": "health_restore",
            "name": "Health Restore",
            "description": f"Restore +3 HP (max {STATE['player'].max_hp})",
            "icon": "❤️",
        },
        {
            "id": "attack_power",
            "name": "Attack Power",
            "description": "+3 Attack (deals 3 more damage per hit)",
            "icon": "⚔️",
        },
        {
            "id": "noodles",
            "name": "Organic Crispy Noodles",
            "description": "+3 Attack + 10% critical strike chance (double damage)",
            "icon": "🍜",
        },
        {
            "id": "aegis",
            "name": "Everbloom Aegis",
            "description": "Permanent 50% damage reduction passive shield",
            "icon": "🥻",
        },
        {
            "id": "spell",
            "name": "Gateway Of Living Grace",
            "description": "Active force field for 3 turns (50% damage reduction + 30% bonus attack)",
            "icon": "🪄",
        },
        {
            "id": "eco_blaster",
            "name": "Eco Blaster",
            "description": "Remove one wrong answer (gain 1 use)",
            "icon": "𒄉",
        }
    ]
    
    # Randomly select 3 rewards from the pool
    return random.sample(all_rewards, 3)


@app.route("/api/scene", methods=["POST"])
def scene():
    if not STATE.get("active"):
        return jsonify({"error": "Game not started."}), 400

    data = request.get_json(silent=True) or {}
    boss_index = int(data.get("boss_index", STATE["current_boss_index"]))
    boss_index = max(0, min(boss_index, len(STATE["bosses"]) - 1))
    STATE["current_boss_index"] = boss_index

    boss_dict = STATE["bosses"][boss_index]
    difficulty = STATE["difficulty"]

    # Try prefetch queue first for instant response
    scene_raw = _get_prefetched_scene(boss_index)
    if not scene_raw:
        boss = Boss(**{k: boss_dict[k] for k in ["name", "category", "hp"]})
        scene_raw = _ask_model_for_scene(boss, STATE["player"], difficulty)
        scene_raw = {"boss_index": boss_index, **scene_raw}
    STATE["current_scene_raw"] = scene_raw

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
        # Use instant fallback instead of blocking on API
        scene_raw = _fallback_scene(
            boss, STATE["player"],
            _difficulty_settings(difficulty)["sustainable_choices"]
        )
        scene_raw = {"boss_index": boss_index, **scene_raw}
        STATE["current_scene_raw"] = scene_raw

    selected = next((c for c in scene_raw["choices"] if c["id"] == choice_id), None)
    if not selected:
        return jsonify({"error": "Choice not found."}), 400

    dp = int(selected["delta_player"]["hp"])
    db = int(selected["delta_boss"]["hp"])
    was_sustainable = bool(selected["is_sustainable"])

    # === DAMAGE TO PLAYER ===
    # Apply shield: each level reduces 20% of incoming damage
    if dp < 0:
        shield_reduction = int(dp * 0.2 * STATE["player"].shield)  # 20% per level
        dp = min(0, dp - shield_reduction)  # Shield can't make damage positive
    
    # Apply Aegis: permanent 50% damage reduction
    if STATE["player"].aegis_active and dp < 0:
        dp = int(dp * 0.5)  # Cut damage in half
    
    # Apply force field: 50% damage reduction if active (additional layer)
    if STATE["player"].force_field_turns > 0 and dp < 0:
        dp = int(dp * 0.5)  # Cut damage in half
    
    # === DAMAGE TO BOSS ===
    # Apply attack bonus: increases damage dealt to boss (make db more negative)
    if db < 0:
        db = db - STATE["player"].attack_bonus  # More negative = more damage
        
        # Apply critical strike: chance to double damage
        if STATE["player"].critical_strike_chance > 0:
            if random.random() * 100 < STATE["player"].critical_strike_chance:
                db = db * 2  # Double the damage
        
        # Apply force field attack boost: 30% extra damage for 3 turns
        if STATE["player"].force_field_turns > 0:
            db = int(db * 1.3)  # 30% more negative = more damage
    
    # Decrement force field turns
    if STATE["player"].force_field_turns > 0:
        STATE["player"].force_field_turns -= 1

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
        # Use instant fallback instead of blocking on API;
        # prefetch worker will fill queue with AI scenes for future turns
        next_scene_raw = _fallback_scene(
            boss, STATE["player"],
            _difficulty_settings(difficulty)["sustainable_choices"]
        )
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


@app.route("/api/use_item", methods=["POST"])
def use_item():
    """Activate an item from inventory: noodles, aegis, spell, or eco_blaster."""
    if not STATE.get("active"):
        return jsonify({"error": "Game not started."}), 400

    if STATE.get("pending_reward"):
        return jsonify({"error": "Please claim your reward first!"}), 400

    data = request.get_json(silent=True) or {}
    item_id = str(data.get("item_id", "")).strip().lower()

    if item_id == "noodles":
        if STATE["player"].noodles_charges <= 0:
            return jsonify({"error": "No Noodle charges remaining."}), 400
        STATE["player"].noodles_charges -= 1
        STATE["player"].attack_bonus += 3
        STATE["player"].critical_strike_chance += 10
        return jsonify({
            "outcome": "item_used",
            "item_id": "noodles",
            "message": f"Noodle Power! +3 Attack + {STATE['player'].critical_strike_chance}% Crit!",
            **_get_player_stats(),
        })

    if item_id == "aegis":
        if STATE["player"].aegis_charges <= 0:
            return jsonify({"error": "No Aegis charges remaining."}), 400
        if STATE["player"].aegis_active:
            return jsonify({"error": "Aegis is already active."}), 400
        STATE["player"].aegis_charges -= 1
        STATE["player"].aegis_active = True
        return jsonify({
            "outcome": "item_used",
            "item_id": "aegis",
            "message": "Everbloom Aegis activated! Permanent 50% damage reduction!",
            **_get_player_stats(),
        })

    if item_id == "spell":
        if STATE["player"].spell_charges <= 0:
            return jsonify({"error": "No Spell charges remaining."}), 400
        STATE["player"].spell_charges -= 1
        STATE["player"].force_field_turns = 3
        STATE["player"].attack_bonus += 1
        return jsonify({
            "outcome": "item_used",
            "item_id": "spell",
            "message": "Gateway Of Living Grace! 50% defense + 30% attack for 3 turns!",
            **_get_player_stats(),
        })

    if item_id == "eco_blaster":
        if STATE["player"].eco_blaster_uses <= 0:
            return jsonify({"error": "No Eco Blaster uses remaining."}), 400

        scene_raw = STATE.get("current_scene_raw")
        if not scene_raw:
            return jsonify({"error": "No scene loaded."}), 400

        wrong_answers = [c for c in scene_raw["choices"] if not c.get("is_sustainable", False)]
        if not wrong_answers:
            return jsonify({"error": "No wrong answers available to remove."}), 400

        removed_choice = random.choice(wrong_answers)
        scene_raw["choices"] = [c for c in scene_raw["choices"] if c["id"] != removed_choice["id"]]
        STATE["player"].eco_blaster_uses -= 1

        return jsonify({
            "outcome": "item_used",
            "item_id": "eco_blaster",
            "message": f"Eco Blaster fired! Removed a wrong answer. ({STATE['player'].eco_blaster_uses} left)",
            "removed_choice_id": removed_choice["id"],
            **_get_player_stats(),
            **_scene_for_client(scene_raw),
        })

    return jsonify({"error": f"Unknown item: {item_id}"}), 400


@app.route("/api/claim_reward", methods=["POST"])
def claim_reward():
    """Player claims their reward after defeating a boss."""
    if not STATE.get("active"):
        return jsonify({"error": "Game not started."}), 400
    
    if not STATE.get("pending_reward"):
        return jsonify({"error": "No reward pending."}), 400

    data = request.get_json(silent=True) or {}
    reward_id = str(data.get("reward_id", "")).strip().lower()
    
    valid_rewards = {"shield_boost", "health_restore", "attack_power", "noodles", "aegis", "spell", "eco_blaster"}
    if reward_id not in valid_rewards:
        return jsonify({"error": f"Invalid reward. Choose one of: {', '.join(valid_rewards)}."}), 400

    # Apply the chosen reward
    reward_message = ""
    if reward_id == "shield_boost":
        STATE["player"].shield += 1
        reward_message = f"Shield Level +1! Now taking 20% less damage per level. (Level {STATE['player'].shield})"
    
    elif reward_id == "health_restore":
        old_hp = STATE["player"].hp
        STATE["player"].hp = min(STATE["player"].hp + 3, STATE["player"].max_hp)
        healed = STATE["player"].hp - old_hp
        reward_message = f"Restored {healed} HP! (Now at {STATE['player'].hp}/{STATE['player'].max_hp})"
    
    elif reward_id == "attack_power":
        STATE["player"].attack_bonus += 3
        reward_message = f"Attack Power +3! You now deal {STATE['player'].attack_bonus} bonus damage per hit."
    
    elif reward_id == "noodles":
        STATE["player"].noodles_charges += 1
        reward_message = f"Organic Crispy Noodles added to inventory! ({STATE['player'].noodles_charges} charge(s)) — Activate for +3 Attack + 10% Crit."
    
    elif reward_id == "aegis":
        STATE["player"].aegis_charges += 1
        reward_message = f"Everbloom Aegis added to inventory! ({STATE['player'].aegis_charges} charge(s)) — Activate for permanent 50% damage reduction."
    
    elif reward_id == "spell":
        STATE["player"].spell_charges += 1
        reward_message = f"Gateway Of Living Grace added to inventory! ({STATE['player'].spell_charges} charge(s)) — Activate for 3 turns of 50% defense + 30% attack."
    
    elif reward_id == "eco_blaster":
        STATE["player"].eco_blaster_uses += 1
        reward_message = f"Eco Blaster Charged! You now have {STATE['player'].eco_blaster_uses} use(s). (Removes 1 wrong answer per use.)"

    # Clear pending reward
    STATE["pending_reward"] = False

    # Now advance to next boss
    _clear_prefetch()
    
    STATE["current_boss_index"] = min(STATE["current_boss_index"] + 1, len(STATE["bosses"]) - 1)
    next_boss_dict = STATE["bosses"][STATE["current_boss_index"]]
    difficulty = STATE["difficulty"]

    # Use fallback scene instantly, then let prefetch fill real AI scenes
    # This makes claim_reward respond in <50ms instead of 1-3s
    next_boss = Boss(**{k: next_boss_dict[k] for k in ["name", "category", "hp"]})
    next_scene_raw = _fallback_scene(
        next_boss, STATE["player"],
        _difficulty_settings(difficulty)["sustainable_choices"]
    )
    STATE["current_scene_raw"] = {"boss_index": STATE["current_boss_index"], **next_scene_raw}
    image_data_url = _get_boss_image(next_boss_dict)

    # Start pre-fetching AI-quality scenes for the new boss immediately
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


@app.route("/api/prefetch_status", methods=["GET"])
def prefetch_status():
    """Debug endpoint: shows current prefetch queue status.
    Useful to verify scenes are being preloaded.
    
    Visit: http://localhost:5000/api/prefetch_status
    """
    with _prefetch_lock:
        queue_size = len(_prefetch_queue)
    
    return jsonify({
        "prefetch_queue_size": queue_size,
        "prefetch_target": _prefetch_target,
        "prefetch_running": _prefetch_running,
        "queue_full": queue_size >= _prefetch_target,
        "game_active": STATE.get("active", False),
        "current_boss": STATE.get("bosses", [{}])[STATE.get("current_boss_index", 0)].get("name", "No boss") if STATE.get("bosses") else "No bosses",
    })


@app.route("/api/trigger_prefetch", methods=["POST"])
def trigger_prefetch():
    """Frontend calls this while the user reads a scene to ensure
    future scenes are being generated in the background.
    Returns immediately with the current queue status.
    """
    if not STATE.get("active"):
        return jsonify({"status": "inactive"}), 200

    _start_prefetch()

    with _prefetch_lock:
        queue_size = len(_prefetch_queue)

    return jsonify({
        "status": "ok",
        "queue_size": queue_size,
        "target": _prefetch_target,
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
# Local fact bank eliminates API call latency entirely (~0ms vs ~1-3s)
_FACT_BANK: List[str] = [
    "Recycling one aluminum can saves enough energy to run a TV for 3 hours!",
    "A single tree can absorb up to 48 pounds of CO2 per year.",
    "Turning off the tap while brushing your teeth saves up to 8 gallons of water a day!",
    "Walking or biking instead of driving for short trips can cut your carbon footprint by 75%.",
    "Composting food scraps can reduce household waste by up to 30%.",
    "LED bulbs use 75% less energy than traditional incandescent bulbs.",
    "The average person generates about 4.4 pounds of trash per day.",
    "Plastic takes up to 500 years to decompose in a landfill.",
    "A leaky faucet can waste over 3,000 gallons of water per year.",
    "Reusing a single plastic bag saves enough energy to power a light bulb for 11 hours.",
    "If every American recycled one-tenth of their newspapers, we'd save 25 million trees a year.",
    "The ocean absorbs about 30% of the CO2 produced by humans.",
    "Spending just 20 minutes outside in nature can lower stress hormone levels.",
    "A full dishwasher uses less water than washing dishes by hand.",
    "Glass can be recycled endlessly without any loss in quality.",
    "One bus can replace 40 cars on the road during rush hour.",
    "Planting native wildflowers helps pollinators like bees and butterflies thrive.",
    "Using a reusable water bottle can save an average of 156 plastic bottles per year.",
    "Eating one meat-free meal per week is like taking your car off the road for 320 miles.",
    "A 5-minute shower uses about 10-25 gallons of water.",
    "Unplugging electronics when not in use can save up to 10% on your electricity bill.",
    "Paper can be recycled up to 7 times before the fibers become too short.",
    "Rainwater harvesting can reduce household water use by 40-50%.",
    "The fashion industry produces 10% of global carbon emissions.",
    "Buying local food reduces transportation emissions and supports your community.",
    "A single mature tree provides enough oxygen for two people per year.",
    "About 8 million tons of plastic enter the oceans every year.",
    "Solar panels can reduce a home's carbon footprint by 80%.",
    "Thrift shopping keeps clothing out of landfills and saves resources.",
    "Worm composting can process food scraps in as little as 2-3 months.",
]


@app.route("/api/fact", methods=["GET"])
def fact():
    # Instant response from local bank — no API call needed
    return jsonify({"fact": random.choice(_FACT_BANK)})

if __name__ == "__main__":
    app.run(debug=True, threaded=True, port=5001)
