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

const sceneText = document.getElementById("scene_text");
const choicesEl = document.getElementById("choices");
const turnFeedback = document.getElementById("turn_feedback");
const sustainabilityFact = document.getElementById("sustainability_fact");

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

// Story segments for the loading screen
const STORY_SEGMENTS = [
  {
    text: "STORY_SEGEMENT 1 GOES HERE",
    status: "Scanning threat levels...",
    progress: 15
  },
  {
    text: "STORY_SEGEMENT 2 GOES HERE",
    status: "Analyzing enemy patterns...",
    progress: 35
  },
  {
    text: "STORY_SEGEMENT 3 GOES HERE",
    status: "Calibrating sustainable attacks...",
    progress: 55
  },
  {
    text: "STORY_SEGEMENT 4 GOES HERE",
    status: "Preparing battle arena...",
    progress: 75
  },
  {
    text: "STORY_SEGEMENT 5 GOES HERE",
    status: "Loading first boss...",
    progress: 90
  }
];

function typeWriter(element, text, speed = 30) {
  return new Promise((resolve) => {
    let i = 0;
    element.innerHTML = '<span class="cursor"></span>';
    
    function type() {
      if (i < text.length) {
        element.innerHTML = text.substring(0, i + 1) + '<span class="cursor"></span>';
        i++;
        typewriterTimeout = setTimeout(type, speed);
      } else {
        setTimeout(() => {
          element.innerHTML = text;
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

  sceneText.textContent = data.scene ?? "...";
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

async function applyChoice(choiceId) {
  if (inFlight) return;
  inFlight = true;
  setDisabledChoices(true);
  if (turnFeedback) turnFeedback.textContent = "Resolving...";
  let outcome = null;

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

    if (outcome === "victory" || outcome === "player_defeated") {
      setDisabledChoices(true);
      restartBtn.classList.remove("hidden");
      sceneText.textContent = data.message ?? sceneText.textContent;
      if (turnFeedback) turnFeedback.textContent = message;
      await maybeLoadFact();
      return;
    }

    // boss_defeated or continue both include next scene payload
    if (data.player_hp != null) maxPlayerHp = Math.max(maxPlayerHp, Number(data.player_hp) || 1);
    renderGame(data);
    if (turnFeedback) turnFeedback.textContent = message;

    if (outcome === "boss_defeated") {
      await maybeLoadFact();
    }
  } catch (err) {
    console.error(err);
    if (turnFeedback) turnFeedback.textContent = "Something went wrong. Try again.";
    setDisabledChoices(false);
  } finally {
    inFlight = false;
    if (outcome !== "victory" && outcome !== "player_defeated") setDisabledChoices(false);
  }
}
