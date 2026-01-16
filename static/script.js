const usernameInput = document.getElementById("username");
const difficultyButtons = document.querySelectorAll(".difficulty");
const startBtn = document.getElementById("startBtn");
const form = document.getElementById("startForm");
const statusEl = document.getElementById("status");
const game_screen = document.getElementById("game_screen")
const start_screen = document.getElementById("start_screen")
const sceneText = document.getElementById("scene-text");
const bossName = document.getElementById("boss_name")
const player_hp = document.getElementById("player_hp")
const boss_hp = document.getElementById("boss_hp")
const gamestatus = document.getElementById("gameStatus")
const choicesContainer = document.getElementById("choices")
const player_hp_bar = document.getElementById("player_hp_bar")
const boss_hp_bar = document.getElementById("boss_hp_bar")

let selectedDifficulty = null;
let currentBossIndex = 0;
let bosses = [];
let playerStats = { hp: 3, maxHp: 3 };
let sceneCount = 0;
let bossesDefeated = 0;

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
  setStatus("Starting game...");

  try {
    const res = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, difficulty: selectedDifficulty }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Start failed (${res.status}): ${text}`);
    }

    const data = await res.json();
    bosses = data.bosses ?? [];
    playerStats = { hp: data.player_hp ?? 3, maxHp: data.player_hp ?? 3 };
    currentBossIndex = 0;
    sceneCount = 0;
    localStorage.setItem("bosses", JSON.stringify(bosses));
    localStorage.setItem("player_hp", data.player_hp ?? "3");

    start_screen.classList.add("hidden");
    game_screen.classList.remove("hidden");
    game_screen.setAttribute("aria-hidden", "false");
    setStatus("Loading first scene...");

    loadFirstStage();
  } catch (err) {
    console.error(err);
    setStatus("Could not start game. Please try again.");
  } finally {
    updateStartButton();
  }
});

async function loadFirstStage() {
  if (!bosses.length) {
    setStatus("No bosses found. Please restart.")
    return;
  }
  await loadBattle(0);
}

async function loadBattle(bossIndex) {
  currentBossIndex = bossIndex;
  sceneCount = 0;

  if (bossIndex >= bosses.length) {
    displayGameOver(true);
    return;
  }

  if (playerStats.hp <= 0) {
    displayGameOver(false);
    return;
  }

  await loadScene();
}

async function loadScene() {
  sceneText.textContent = "";
  choicesContainer.innerHTML = "";
  gamestatus.textContent = "Generating scene...";

  try {
    const response = await fetch("/api/scene/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ boss_index: currentBossIndex })
    });

    if (!response.ok) {
      gamestatus.textContent = "Error loading scene";
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let sceneData = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value, { stream: true });
      const lines = text.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const eventData = JSON.parse(line.slice(6));

            if (eventData.type === "chunk") {
              gamestatus.textContent = "Crafting your adventure...";
            } else if (eventData.type === "complete") {
              sceneData = eventData;
              await typewriterEffect(eventData.scene);
              gamestatus.textContent = "";
            } else if (eventData.type === "error") {
              gamestatus.textContent = "Error: " + eventData.message;
            }
          } catch (e) {
            console.log("Parse error:", e);
          }
        }
      }
    }

    if (sceneData) {
      displaySceneFromData(sceneData, currentBossIndex, bosses[currentBossIndex]);
    }
    sceneCount++;

  } catch (err) {
    console.error(err);
    gamestatus.textContent = "Error loading scene. Retrying...";
    await loadSceneFallback();
  }
}

async function typewriterEffect(text) {
  sceneText.textContent = "";
  const words = text.split(" ");
  for (let i = 0; i < words.length; i++) {
    sceneText.textContent += (i > 0 ? " " : "") + words[i];
    await new Promise(r => setTimeout(r, 30));
  }
}

async function loadSceneFallback() {
  const response = await fetch("/api/scene", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ boss_index: currentBossIndex })
  });

  if (!response.ok) {
    gamestatus.textContent = "Error loading scene";
    return;
  }

  const data = await response.json();
  await typewriterEffect(data.scene);
  displaySceneFromData(data, currentBossIndex, bosses[currentBossIndex]);
  sceneCount++;
}

function displayScene(data, bossIndex, boss) {
  start_screen.classList.add("hidden");
  game_screen.classList.remove("hidden");
  game_screen.setAttribute("aria-hidden", "false");

  bossName.textContent = boss.name;

  updateHealthBars();

  sceneText.textContent = data.scene;
  gamestatus.textContent = "";

  renderChoices(data.choices, bossIndex);
}

function displaySceneFromData(data, bossIndex, boss) {
  start_screen.classList.add("hidden");
  game_screen.classList.remove("hidden");
  game_screen.setAttribute("aria-hidden", "false");

  bossName.textContent = boss.name;

  updateHealthBars();

  renderChoices(data.choices, bossIndex);
}

function updateHealthBars() {
  const playerPercent = (playerStats.hp / playerStats.maxHp) * 100;
  player_hp_bar.style.width = playerPercent + "%";
  player_hp.textContent = `${playerStats.hp}/${playerStats.maxHp}`;

  const boss = bosses[currentBossIndex];
  const bossPercent = (boss.hp / 50) * 100;
  boss_hp_bar.style.width = Math.max(0, Math.min(100, bossPercent)) + "%";
  boss_hp.textContent = `${Math.max(0, boss.hp)}/50`;
}

function renderChoices(choices, bossIndex) {
  choicesContainer.innerHTML = "";

  choices.forEach((choice) => {
    const button = document.createElement("button");
    button.className = "choice-btn";
    button.innerHTML = `<span class="choice-id">${choice.id}.</span> ${choice.text}`;

    button.addEventListener("click", async () => {
      button.disabled = true;
      choicesContainer.querySelectorAll(".choice-btn").forEach(b => b.disabled = true);

      await showFactModal(bosses[bossIndex].category);

      await applyChoice(bossIndex, choice, choices);
    });

    choicesContainer.appendChild(button);
  });
}

async function applyChoice(bossIndex, choice, allChoices) {
  try {
    const response = await fetch("/api/apply_choice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        boss_index: bossIndex,
        delta_player: choice.delta_player,
        delta_boss: choice.delta_boss
      })
    });

    if (!response.ok) {
      gamestatus.textContent = "Error applying choice";
      choicesContainer.querySelectorAll(".choice-btn").forEach(b => b.disabled = false);
      return;
    }

    const data = await response.json();
    playerStats.hp = data.player_hp;
    bosses[bossIndex].hp = data.boss_hp;

    updateHealthBars();

    if (bosses[bossIndex].hp <= 0) {
      bossesDefeated++;
      gamestatus.textContent = `Boss defeated! Moving to next battle...`;
      await new Promise(resolve => setTimeout(resolve, 2000));
      await loadBattle(bossIndex + 1);
    } else if (playerStats.hp <= 0) {
      displayGameOver(false);
    } else {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await loadScene();
    }
  } catch (err) {
    console.error(err);
    gamestatus.textContent = "Error processing choice";
    choicesContainer.querySelectorAll(".choice-btn").forEach(b => b.disabled = false);
  }
}

function displayGameOver(won) {
  start_screen.classList.add("hidden");
  game_screen.classList.remove("hidden");
  game_screen.setAttribute("aria-hidden", "false");

  choicesContainer.innerHTML = "";

  const scoreMessage = `\n\n🏆 Score: ${bossesDefeated} boss${bossesDefeated !== 1 ? 'es' : ''} defeated`;
  const username = localStorage.getItem("username") || "Player";

  sceneText.textContent = won
    ? `Congratulations ${username}! You've defeated all bosses and saved the environment!` + scoreMessage
    : `Game Over ${username}! The environmental villains have won.` + scoreMessage;

  gamestatus.innerHTML = `
    <button style="padding: 0.8rem 1.5rem; margin-top: 1rem; background: var(--primary); color: #052e16; border: none; border-radius: 8px; cursor: pointer; font-weight: 700;" onclick="returnToMenu()">
      Return to Menu
    </button>
  `;
}

function returnToMenu() {
  bossesDefeated = 0;
  currentBossIndex = 0;
  sceneCount = 0;
  selectedDifficulty = null;

  difficultyButtons.forEach(b => {
    b.classList.remove("active");
    b.setAttribute("aria-checked", "false");
  });
  usernameInput.value = "";
  startBtn.disabled = true;
  setStatus("");

  game_screen.classList.add("hidden");
  game_screen.setAttribute("aria-hidden", "true");
  start_screen.classList.remove("hidden");
}
const factModal = document.getElementById("factModal");
const factText = document.getElementById("factText");
const closeModalBtn = document.getElementById("closeModalBtn");

closeModalBtn.addEventListener("click", () => {
  factModal.close();
});

async function showFactModal(topic) {
  factModal.showModal();
  factText.textContent = "Loading...";

  try {
    const res = await fetch("/api/fact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic: topic })
    });

    const data = await res.json();
    factText.textContent = data.fact;
  } catch (e) {
    factText.textContent = "Did you know? Small actions add up to big changes!";
  }



  return new Promise(resolve => {
    closeModalBtn.onclick = () => {
      factModal.close();
      resolve();
    };
  });
}
