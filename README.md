# 🌍 EcoGuardian Boss Rush

Welcome to the **Presidential AI Challenge** project! This is a web-based game where you battle environmental villains using sustainability knowledge. 

## 🛠️ Prerequisites

1.  **Python 3.8+**: Make sure you have Python installed. You can download it from [python.org](https://www.python.org/).
2.  **OpenAI API Key**: You will need an API key to generate the dynamic battle scenes.

## 🚀 Setup Instructions

### 1. Download the Code
Download this folder to your computer.

### 2. Open a Terminal
- **Mac/Linux**: Open "Terminal".
- **Windows**: Open "Command Prompt" or "PowerShell".

Navigate to the project folder:
```bash
cd path/to/BOSSRUSH
```

### 3. Create a Virtual Environment (Recommended)
This keeps your project dependencies organized.

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 4. Install Dependencies
Run this command to install Flask and OpenAI libraries:
```bash
pip install -r requirements.txt
```

### 5. Set up your API Key
1. Create a file named `.env` in the same folder as `app.py`.
2. Open it with a text editor and add your key like this:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

## 🎮 Playing the Game

1. Start the server:
```bash
python app.py
```
2. You should see output saying `Running on http://127.0.0.1:5001`.
3. Open your web browser and go to: **[http://127.0.0.1:5001](http://127.0.0.1:5001)**

## 🧪 structure
- `app.py`: The main logic server (Backend).
- `static/`: Contains the style (`styles.css`) and logic (`script.js`) for the website.
- `templates/`: Contains the HTML structure (`index.html`).

Good luck, Guardian! 🌱
