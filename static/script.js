const usernameInput = document.getElementById("username");
const difficultyButtons = document.querySelectorAll(".difficulty");
const startBtn = document.getElementById("startBtn");
const form = document.getElementById("startForm");
const statusEl = document.getElementById("status");
const gameScreen = document.getElementById("game_screen");
const startScreen = document.getElementById("start_screen");
const loadingScreen = document.getElementById("loading_screen");

const progressText = document.getElementById("progress_text");
const restartBtn = document.getElementById("restartBtn");

const bossName = document.getElementById("boss_name");
const bossCategory = document.getElementById("boss_category");
const bossHpText = document.getElementById("boss_hp");
const bossHpBar = document.getElementById("boss_hp_bar");
const bossImage = document.getElementById("boss_image");

const playerHpText = document.getElementById("player_hp");
const playerHpBar = document.getElementById("player_hp_bar");
const playerShieldText = document.getElementById("player_shield");
const playerAttackText = document.getElementById("player_attack");

const sceneText = document.getElementById("scene_text");
const choicesEl = document.getElementById("choices");
const turnFeedback = document.getElementById("turn_feedback");
const sustainabilityFact = document.getElementById("sustainability_fact");
const rewardModal = document.getElementById("reward_modal");
const rewardOptions = document.getElementById("reward_options");
const rewardMessage = document.getElementById("reward_message");
const victoryScreen = document.getElementById("victory_screen");
const defeatScreen = document.getElementById("defeat_screen");
const damageOverlay = document.getElementById("damage_overlay");

// Item bar elements
const itemBar = document.getElementById("item_bar");
const itemSlots = {
  noodles:     { btn: document.getElementById("item_noodles"),      count: document.getElementById("item_noodles_count") },
  aegis:       { btn: document.getElementById("item_aegis"),        count: document.getElementById("item_aegis_count") },
  spell:       { btn: document.getElementById("item_spell"),        count: document.getElementById("item_spell_count") },
  eco_blaster: { btn: document.getElementById("item_eco_blaster"),  count: document.getElementById("item_eco_blaster_count") },
};

// Loading screen elements
const loadingTitle = document.getElementById("loading_title");
const storyText = document.getElementById("story_text");
const loadingBarFill = document.getElementById("loading_bar_fill");
const loadingStatus = document.getElementById("loading_status");

let selectedDifficulty = null;
let maxPlayerHp = 1;
let maxBossHp = 1;
let inFlight = false;
let currentBossName = null;
let typewriterTimeout = null;
let prefetchInterval = null;  // Background prefetch polling

// Story segments for the loading screen
const STORY_SEGMENTS = [
  {
    text: "Once upon a time, a powerful necromancer released environmental disasters as monsters that could attack the world. ",
    status: "Scanning threat levels...",
    progress: 15
  },
  {
    text: "This was because he was evil and displeased how well the humans were living. These monsters drove chaos throughout the world and made the world unsustainable, and eventually, the humans chose one brave player to face the monsters. YOU!",
      status: "Analyzing enemy patterns...",
    progress: 35
  },
  {
    text: "You also notice that every time you start to do an environmentally friendly task, you gain stronger powers, motivating you even more to complete sustainable tasks",
    status: "Calibrating sustainable attacks...",
    progress: 55
  },
  {
    text: "Finally, you reach an extremely difficult task(ridding the world of all unsustainable minions) from the leaders of the world, or the final task. You must use all the knowledge that you have gained along the way to complete this. With your attacks, you unleash the full powers of every environmental attack you have, and you become a master of ridding the world of unsustainable minions.",
    status: "Preparing battle arena...",
    progress: 75
  },
  {
    text: "You fought hard. You encountered many hardships. but one day, you hear a giant rumble... Now it is time to fight the final pollution bosses.",
    status: "Loading first boss...",
    progress: 90
  }
];

function typeWriter(element, text, speed = 30) {
  return new Promise((resolve) => {
    let i = 0;
    // Use a text node + cursor span to avoid rebuilding innerHTML every frame
    const textNode = document.createTextNode("");
    const cursor = document.createElement("span");
    cursor.className = "cursor";
    element.innerHTML = "";
    element.appendChild(textNode);
    element.appendChild(cursor);
    
    function type() {
      if (i < text.length) {
        textNode.textContent = text.substring(0, i + 1);
        i++;
        typewriterTimeout = setTimeout(type, speed);
      } else {
        setTimeout(() => {
          cursor.remove();
          resolve();
        }, 500);
      }
    }
    type();
  });
}

async function showLoadingScreen(username) {
  startScreen.classList.add("hidden");
  loadingScreen.classList.remove("hidden");
  loadingScreen.setAttribute("aria-hidden", "false");
  
  // Personalize the title
  loadingTitle.textContent = `${username}, Your Mission Awaits...`;
  
  storyText.innerHTML = "";
  loadingBarFill.style.width = "0%";
  loadingStatus.textContent = "Initializing...";
}

async function runStorySequence() {
  for (const segment of STORY_SEGMENTS) {
    loadingStatus.textContent = segment.status;
    loadingBarFill.style.width = segment.progress + "%";
    // Trigger prefetch during each segment to fill the scene queue
    triggerPrefetch();
    await typeWriter(storyText, segment.text, 25);
    await new Promise(r => setTimeout(r, 800));
  }
}

function hideLoadingScreen() {
  if (typewriterTimeout) {
    clearTimeout(typewriterTimeout);
    typewriterTimeout = null;
  }
  
  loadingBarFill.style.width = "100%";
  loadingStatus.textContent = "Battle ready!";
  
  setTimeout(() => {
    loadingScreen.classList.add("hidden");
    loadingScreen.setAttribute("aria-hidden", "true");
    gameScreen.classList.remove("hidden");
    gameScreen.classList.add("fade-in");
    gameScreen.setAttribute("aria-hidden", "false");
    restartBtn.classList.remove("hidden");
  }, 400);
}

function updateStartButton() {
  const hasUsername = usernameInput.value.trim().length > 0;
  startBtn.disabled = !(hasUsername && selectedDifficulty);
}

function setStatus(message) {
  if (!statusEl) return;
  statusEl.textContent = message ?? "";
}

difficultyButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    difficultyButtons.forEach((b) => {
      b.classList.remove("active");
      b.setAttribute("aria-checked", "false");
    });

    btn.classList.add("active");
    btn.setAttribute("aria-checked", "true");
    selectedDifficulty = btn.dataset.value;

    updateStartButton();
  });
});

usernameInput.addEventListener("input", updateStartButton);

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = usernameInput.value.trim();
  if (!username || !selectedDifficulty) return;

  localStorage.setItem("username", username);
  localStorage.setItem("difficulty", selectedDifficulty);

  startBtn.disabled = true;
  
  showLoadingScreen(username);
  
  const storyPromise = runStorySequence();
  const apiPromise = fetch("/api/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, difficulty: selectedDifficulty }),
  });

  try {
    const [_, res] = await Promise.all([storyPromise, apiPromise]);

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Start failed (${res.status}): ${text}`);
    }

    const data = await res.json();
    maxPlayerHp = Number(data.player_hp ?? 1) || 1;
    maxBossHp = Number(data.boss?.hp ?? 1) || 1;
    
    await new Promise(r => setTimeout(r, 600));
    
    hideLoadingScreen();
    renderGameAfterLoading(data);
  } catch (err) {
    console.error(err);
    loadingScreen.classList.add("hidden");
    startScreen.classList.remove("hidden");
    setStatus("Could not start game. Please try again.");
    updateStartButton();
  }
});

restartBtn?.addEventListener("click", () => {
  window.location.reload();
});

document.getElementById("victoryRestartBtn")?.addEventListener("click", () => {
  window.location.reload();
});

document.getElementById("defeatRestartBtn")?.addEventListener("click", () => {
  window.location.reload();
});

function showGameScreen() {
  startScreen.classList.add("hidden");
  loadingScreen.classList.add("hidden");
  gameScreen.classList.remove("hidden");
  gameScreen.setAttribute("aria-hidden", "false");
  restartBtn.classList.remove("hidden");
}

function setBars({ playerHp, bossHp }) {
  const safePlayer = Math.max(0, Number(playerHp ?? 0) || 0);
  const safeBoss = Math.max(0, Number(bossHp ?? 0) || 0);

  playerHpText.textContent = `${safePlayer}`;
  bossHpText.textContent = `${safeBoss}`;

  const playerPct = Math.max(0, Math.min(100, (safePlayer / Math.max(1, maxPlayerHp)) * 100));
  const bossPct = Math.max(0, Math.min(100, (safeBoss / Math.max(1, maxBossHp)) * 100));

  playerHpBar.style.width = `${playerPct}%`;
  bossHpBar.style.width = `${bossPct}%`;
}

function setPlayerStats(data, animate = false) {
  if (playerShieldText && data.player_shield != null) {
    const oldValue = parseInt(playerShieldText.textContent) || 0;
    playerShieldText.textContent = data.player_shield;
    playerShieldText.parentElement.style.display = data.player_shield > 0 ? "flex" : "none";
    
    // Animate if value increased
    if (animate && data.player_shield > oldValue) {
      playerShieldText.parentElement.classList.add("stat-pulse");
      setTimeout(() => playerShieldText.parentElement.classList.remove("stat-pulse"), 600);
    }
  }
  if (playerAttackText && data.player_attack_bonus != null) {
    const oldValue = parseInt(playerAttackText.textContent) || 0;
    playerAttackText.textContent = `+${data.player_attack_bonus}`;
    playerAttackText.parentElement.style.display = data.player_attack_bonus > 0 ? "flex" : "none";
    
    // Animate if value increased
    if (animate && data.player_attack_bonus > oldValue) {
      playerAttackText.parentElement.classList.add("stat-pulse");
      setTimeout(() => playerAttackText.parentElement.classList.remove("stat-pulse"), 600);
    }
  }
  if (data.player_max_hp) {
    maxPlayerHp = Math.max(maxPlayerHp, data.player_max_hp);
  }
  // Always sync item bar with latest data
  updateItemBar(data);
}

/**
 * Update the item bar to reflect current charges from server data.
 * Shows/hides each slot and the bar itself.
 */
function updateItemBar(data) {
  const charges = {
    noodles:     data.player_noodles_charges     ?? 0,
    aegis:       data.player_aegis_charges       ?? 0,
    spell:       data.player_spell_charges       ?? 0,
    eco_blaster: data.player_eco_blaster_uses    ?? 0,
  };

  let anyVisible = false;

  for (const [id, slot] of Object.entries(itemSlots)) {
    const c = charges[id] || 0;
    if (!slot.btn) continue;

    if (c > 0) {
      slot.btn.classList.remove("hidden");
      slot.btn.disabled = false;
      slot.count.textContent = c;
      anyVisible = true;

      // Disable aegis button if already permanently active
      if (id === "aegis" && data.player_aegis_active) {
        slot.btn.classList.add("item-active-permanent");
        slot.btn.disabled = true;
        slot.btn.title = "Aegis already active";
      } else {
        slot.btn.classList.remove("item-active-permanent");
      }
    } else {
      // Keep showing aegis slot if permanently active (greyed visual)
      if (id === "aegis" && data.player_aegis_active) {
        slot.btn.classList.remove("hidden");
        slot.btn.classList.add("item-active-permanent");
        slot.btn.disabled = true;
        slot.count.textContent = "✓";
        anyVisible = true;
      } else {
        slot.btn.classList.add("hidden");
      }
    }
  }

  // Show/hide force field turn indicator on spell button
  if (data.player_force_field_turns > 0 && itemSlots.spell.btn) {
    itemSlots.spell.btn.classList.add("item-timed-active");
    itemSlots.spell.btn.dataset.turns = data.player_force_field_turns;
  } else if (itemSlots.spell.btn) {
    itemSlots.spell.btn.classList.remove("item-timed-active");
  }

  if (itemBar) {
    itemBar.classList.toggle("hidden", !anyVisible);
  }
}

/**
 * Activate an item — call backend, play animation, update UI.
 */
let itemInFlight = false;
async function useItem(itemId) {
  if (itemInFlight || inFlight) return;
  itemInFlight = true;

  // Disable the clicked button immediately
  const slot = itemSlots[itemId];
  if (slot?.btn) slot.btn.disabled = true;

  try {
    const res = await fetch("/api/use_item", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_id: itemId }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error || "Failed to use item.");
    }

    // Play item activation animation
    playItemAnimation(itemId, data);

    // Update stats & item bar
    setPlayerStats(data, true);

    // If eco_blaster removed a choice, update choices
    if (itemId === "eco_blaster" && data.removed_choice_id) {
      const removedBtn = choicesEl.querySelector(`[data-choice-id="${data.removed_choice_id}"]`);
      if (removedBtn) {
        removedBtn.classList.add("choice-removed");
        setTimeout(() => removedBtn.remove(), 500);
      }
      // Also update the choices with the new scene data if provided
      if (data.choices) {
        setTimeout(() => setChoices(data.choices), 550);
      }
    }

    // Show notification
    showEquippedNotification(itemId, data.message || "Item activated!");

    if (turnFeedback) turnFeedback.textContent = data.message || "";

  } catch (err) {
    console.error(err);
    if (turnFeedback) turnFeedback.textContent = err.message || "Failed to use item.";
    // Re-enable button on error
    if (slot?.btn) slot.btn.disabled = false;
  } finally {
    itemInFlight = false;
  }
}

/**
 * Play a visual animation for each item type.
 */
function playItemAnimation(itemId, data) {
  const overlay = damageOverlay;
  if (!overlay) return;

  // Create a full-screen fx element
  const fx = document.createElement("div");
  fx.className = `item-fx item-fx-${itemId}`;

  switch (itemId) {
    case "noodles":
      fx.innerHTML = `<div class="fx-icon">🍜</div><div class="fx-label">+3 ATK · +10% CRIT</div>`;
      flashPanel(".player-panel", "boss-damage"); // green flash on player
      break;
    case "aegis":
      fx.innerHTML = `<div class="fx-icon">🥻</div><div class="fx-label">AEGIS SHIELD ON</div>`;
      flashPanel(".player-panel", "aegis-flash");
      break;
    case "spell":
      fx.innerHTML = `<div class="fx-icon">🪄</div><div class="fx-label">FORCE FIELD · 3 TURNS</div>`;
      flashPanel(".player-panel", "spell-flash");
      break;
    case "eco_blaster":
      fx.innerHTML = `<div class="fx-icon">𒄉</div><div class="fx-label">BLAST!</div>`;
      flashPanel(".choices-grid", "blast-flash");
      break;
  }

  overlay.appendChild(fx);
  fx.addEventListener("animationend", () => fx.remove());
  setTimeout(() => fx.remove(), 1600); // fallback cleanup
}

// Attach click handlers to item slots
for (const [id, slot] of Object.entries(itemSlots)) {
  if (slot.btn) {
    slot.btn.addEventListener("click", () => useItem(id));
  }
}

function showEquippedNotification(rewardId, message) {
  // Create floating notification
  const notification = document.createElement("div");
  notification.className = "equipped-notification";
  
  const iconMap = {
    shield_boost: "🛡️", shield: "🛡️",
    attack_power: "⚔️", attack: "⚔️",
    health_restore: "❤️",
    noodles: "🍜",
    aegis: "🥻",
    spell: "🪄",
    eco_blaster: "𒄉",
  };
  const icon = iconMap[rewardId] || "✨";
  notification.innerHTML = `<span class="equipped-icon">${icon}</span><span class="equipped-text">${message}</span>`;
  
  document.body.appendChild(notification);
  
  // Trigger animation
  setTimeout(() => notification.classList.add("show"), 10);
  
  // Remove after animation
  setTimeout(() => {
    notification.classList.remove("show");
    setTimeout(() => notification.remove(), 300);
  }, 2500);
}

function showRewardModal(data) {
  if (!rewardModal || !rewardOptions) return;
  
  rewardModal.classList.remove("hidden");
  rewardOptions.innerHTML = "";
  
  if (rewardMessage) {
    rewardMessage.textContent = data.message || "Choose your reward!";
  }
  
  const rewards = data.rewards || [];
  rewards.forEach((reward) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "reward-btn";
    btn.innerHTML = `
      <span class="reward-icon">${reward.icon}</span>
      <span class="reward-name">${reward.name}</span>
      <span class="reward-desc">${reward.description}</span>
    `;
    btn.addEventListener("click", () => claimReward(reward.id));
    rewardOptions.appendChild(btn);
  });
}

function hideRewardModal() {
  if (rewardModal) {
    rewardModal.classList.add("hidden");
  }
}

async function claimReward(rewardId) {
  if (inFlight) return;
  inFlight = true;
  
  // Disable reward buttons
  const btns = rewardOptions?.querySelectorAll("button") || [];
  btns.forEach(b => b.disabled = true);
  
  try {
    const res = await fetch("/api/claim_reward", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reward_id: rewardId }),
    });
    
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error || "Failed to claim reward.");
    }
    
    hideRewardModal();
    
    // Update max HP if needed
    if (data.player_max_hp) maxPlayerHp = data.player_max_hp;
    
    // Show equipped notification
    showEquippedNotification(rewardId, data.reward_message || "Reward equipped!");
    
    // Update stats with animation
    setPlayerStats(data, true);
    
    // Render next boss
    renderGame(data);
    
    // Load a fact for the new boss (fire-and-forget, don't block rendering)
    maybeLoadFact();
    
  } catch (err) {
    console.error(err);
    if (turnFeedback) turnFeedback.textContent = "Failed to claim reward. Try again.";
    btns.forEach(b => b.disabled = false);
  } finally {
    inFlight = false;
  }
}

function setChoices(choices) {
  choicesEl.innerHTML = "";
  (choices ?? []).forEach((c) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "choice";
    btn.dataset.choiceId = c.id;
    btn.textContent = `${c.id}. ${c.text}`;
    btn.addEventListener("click", () => applyChoice(c.id));
    choicesEl.appendChild(btn);
  });
}

function setDisabledChoices(disabled) {
  choicesEl.querySelectorAll("button.choice").forEach((b) => {
    b.disabled = Boolean(disabled);
  });
}

/**
 * Disable/enable all item buttons (prevents use during choice resolution).
 */
function setItemsDisabled(disabled) {
  for (const slot of Object.values(itemSlots)) {
    if (slot.btn && !slot.btn.classList.contains("hidden")) {
      slot.btn.disabled = Boolean(disabled);
    }
  }
}

/**
 * Trigger background prefetch so scenes generate while user reads.
 * Called once when a scene starts rendering, then periodically.
 */
function triggerPrefetch() {
  fetch("/api/trigger_prefetch", { method: "POST" })
    .then(r => r.json())
    .then(data => {
      // Stop polling if queue is already full
      if (data.queue_size >= data.target) {
        stopPrefetchPolling();
      }
    })
    .catch(() => {});
}

function startPrefetchPolling() {
  stopPrefetchPolling();
  // Trigger immediately, then every 4 seconds while user reads
  triggerPrefetch();
  prefetchInterval = setInterval(triggerPrefetch, 4000);
}

function stopPrefetchPolling() {
  if (prefetchInterval) {
    clearInterval(prefetchInterval);
    prefetchInterval = null;
  }
}

async function typewriterScene(element, text, speed = 40) {
  return new Promise((resolve) => {
    let i = 0;
    // Use a text node + cursor to avoid innerHTML rebuild every frame
    const textNode = document.createTextNode("");
    const cursor = document.createElement("span");
    cursor.className = "scene-cursor";
    element.innerHTML = "";
    element.appendChild(textNode);
    element.appendChild(cursor);
    
    // Hide choices container during animation
    choicesEl.style.display = "none";

    // Start prefetching while user reads the typewriter text
    startPrefetchPolling();
    
    function type() {
      if (i < text.length) {
        textNode.textContent = text.substring(0, i + 1);
        i++;
        typewriterTimeout = setTimeout(type, speed);
      } else {
        // Animation complete - show clean text and reveal choices
        setTimeout(() => {
          cursor.remove();
          choicesEl.style.display = "";  // Show choices
          setDisabledChoices(false);  // Enable choices
          resolve();
        }, 300);
      }
    }
    type();
  });
}

function renderGame(data) {
  showGameScreen();
  setStatus("");
  renderGameData(data);
}

function renderGameAfterLoading(data) {
  setStatus("");
  renderGameData(data);
}

function renderGameData(data) {
  const boss = data.boss ?? {};
  bossName.textContent = boss.name ?? "Boss";
  bossCategory.textContent = boss.category ?? "";

  if (data.boss_image) bossImage.src = data.boss_image;

  if (boss.name && boss.name !== currentBossName) {
    currentBossName = boss.name;
    maxBossHp = Math.max(1, Number(boss.hp ?? 1) || 1);
    if (sustainabilityFact) sustainabilityFact.textContent = "";
  }
  setBars({ playerHp: data.player_hp, bossHp: boss.hp });
  setPlayerStats(data);

  // Apply typewriter effect to scene text asynchronously
  const sceneContent = data.scene ?? "...";
  typewriterScene(sceneText, sceneContent);
  
  setChoices(data.choices ?? []);

  const wins = Number(data.wins ?? 0) || 0;
  const required = Number(data.required_wins ?? 0) || 0;
  progressText.textContent = required ? `Wins: ${wins}/${required}` : `Wins: ${wins}`;

  if (turnFeedback) turnFeedback.textContent = "";
}

async function maybeLoadFact() {
  try {
    const res = await fetch("/api/fact");
    if (!res.ok) return;
    const data = await res.json();
    if (data?.fact) sustainabilityFact.textContent = `Fact: ${data.fact}`;
  } catch {
    // ignore
  }
}

/**
 * Show a floating damage number near a target element.
 * @param {string} targetSelector - CSS selector for the element to anchor near
 * @param {string} text - The damage text (e.g. "-12")
 * @param {string} type - "boss-damage" (green) or "player-damage" (red)
 */
function showDamageNumber(targetSelector, text, type) {
  const target = document.querySelector(targetSelector);
  if (!target || !damageOverlay) return;

  const rect = target.getBoundingClientRect();
  const num = document.createElement("div");
  num.className = `damage-number ${type}`;
  num.textContent = text;

  // Position near center of target with slight randomness
  const offsetX = (Math.random() - 0.5) * 40;
  num.style.left = `${rect.left + rect.width / 2 + offsetX}px`;
  num.style.top = `${rect.top + rect.height * 0.3}px`;

  damageOverlay.appendChild(num);

  // Remove after animation completes
  num.addEventListener("animationend", () => num.remove());
  setTimeout(() => num.remove(), 1200); // Fallback cleanup
}

/**
 * Flash a panel element with a colour class briefly.
 */
function flashPanel(selector, type) {
  const el = document.querySelector(selector);
  if (!el) return;
  const classMap = {
    "boss-damage":  "flash-green",
    "player-damage": "flash-red",
    "aegis-flash":  "aegis-flash",
    "spell-flash":  "spell-flash",
    "blast-flash":  "blast-flash",
  };
  const cls = classMap[type] || "flash-green";
  el.classList.add(cls);
  setTimeout(() => el.classList.remove(cls), 600);
}

/**
 * Show victory screen with stats and fact.
 */
function showVictoryScreen(data) {
  const msg = document.getElementById("victory_message");
  const stats = document.getElementById("victory_stats");
  const factEl = document.getElementById("victory_fact");
  if (msg) msg.textContent = data.message || "Victory! You defeated all the bosses!";
  if (stats) stats.textContent = `Bosses defeated: ${data.wins || 0}/${data.required_wins || 0}`;
  if (factEl) {
    fetch("/api/fact").then(r => r.json()).then(d => {
      if (d?.fact) factEl.textContent = d.fact;
    }).catch(() => {});
  }
  victoryScreen?.classList.remove("hidden");
  gameScreen.classList.add("hidden");
}

/**
 * Show defeat screen with stats and fact.
 */
function showDefeatScreen(data) {
  const msg = document.getElementById("defeat_message");
  const stats = document.getElementById("defeat_stats");
  const factEl = document.getElementById("defeat_fact");
  if (msg) msg.textContent = data.message || "You ran out of HP!";
  if (stats) {
    const bossName = data.boss?.name || "the boss";
    stats.textContent = `Defeated by: ${bossName}`;
  }
  if (factEl) {
    fetch("/api/fact").then(r => r.json()).then(d => {
      if (d?.fact) factEl.textContent = d.fact;
    }).catch(() => {});
  }
  defeatScreen?.classList.remove("hidden");
  gameScreen.classList.add("hidden");
}

async function applyChoice(choiceId) {
  if (inFlight || itemInFlight) return;
  inFlight = true;
  setDisabledChoices(true);
  setItemsDisabled(true);
  if (turnFeedback) turnFeedback.textContent = "Resolving...";
  let outcome = null;

  // Stop prefetch polling while we process the choice
  stopPrefetchPolling();

  try {
    const res = await fetch("/api/apply_choice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ choice_id: choiceId }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error || "Choice failed.");
    }

    outcome = data.outcome ?? null;
    const message = data.message ?? "";
    const wasSustainable = data.was_sustainable ?? false;

    // Update player stats (updateItemBar runs inside, so re-disable items after)
    setPlayerStats(data);
    setItemsDisabled(true);

    // === DAMAGE ANIMATIONS ===
    if (wasSustainable) {
      // Green damage on boss
      const bossDmg = data.boss ? (maxBossHp - Math.max(0, Number(data.boss.hp ?? 0))) : 0;
      showDamageNumber(".boss-image", message, "boss-damage");
      flashPanel(".boss-panel", "boss-damage");
    } else {
      // Red damage on player
      showDamageNumber(".player-panel", message, "player-damage");
      flashPanel(".player-panel", "player-damage");
    }

    // Brief pause to let the animation play before updating UI
    await new Promise(r => setTimeout(r, 600));

    if (outcome === "victory") {
      showVictoryScreen(data);
      return;
    }

    if (outcome === "player_defeated") {
      showDefeatScreen(data);
      return;
    }

    if (outcome === "boss_defeated_choose_reward") {
      // Show reward selection modal
      setDisabledChoices(true);
      sceneText.textContent = "Victory! The boss has been defeated!";
      if (turnFeedback) turnFeedback.textContent = "";
      showRewardModal(data);
      return;
    }

    // continue - includes next scene payload
    if (data.player_hp != null) maxPlayerHp = Math.max(maxPlayerHp, Number(data.player_hp) || 1);
    renderGame(data);
    if (turnFeedback) turnFeedback.textContent = message;
  } catch (err) {
    console.error(err);
    if (turnFeedback) turnFeedback.textContent = "Something went wrong. Try again.";
    setDisabledChoices(false);
  } finally {
    inFlight = false;
    if (outcome !== "victory" && outcome !== "player_defeated" && outcome !== "boss_defeated_choose_reward") {
      setDisabledChoices(false);
    }
    setItemsDisabled(false);
  }
}
