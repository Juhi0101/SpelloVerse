# 🌌 **SpelloVerse — A Space-Themed Word Puzzle Game**
*A desktop game by Juhi Gupta*

---

## ✨ Overview  
**SpelloVerse** is a desktop word-puzzle adventure built with **Python + Pygame**.  
It blends the satisfying tile-matching feel of **Bejeweled** with the word-forming fun of **Bookworm Adventures**, wrapped in a soft neon **space-themed UI**.

The game is fast, beautiful, and educational — helping players improve vocabulary while having fun.

---

## 🚀 Game Modes

### 🪐 **Mode 1 — Gem Reveal (Match-3 + Word Pop)**  
Match 3+ gems → reveal an English word → score points.  
Features:
- Swap & match like Bejeweled  
- Word + meaning displayed on HUD  
- Neon letter-pop animation  
- Gem falling physics  
- Infinite reshuffling (no dead boards)  

💡 Great for quick, reflexive gameplay.

---

### 🌠 **Mode 2 — Trail Spell (Bookworm-style chain building)**  
Drag across adjacent tiles to form words.

Features:
- Smooth neon trail while dragging  
- Dictionary-validated words  
- Score + audio pronunciation  
- Red flash for invalid paths  
- Gravity pulls letters downward  

💡 Relaxing, strategic gameplay.

---

## 🔊 Features

- Pastel neon **space aesthetic**  
- Transparent floating **HUD**  
- Smooth gem & letter animations  
- Built-in **dictionary with meanings**  
- Offline **word pronunciation**  
- Bad-swap sound feedback  
- Multiple **player profiles**  
- Separate **high scores per mode**

---

## 🛠 Tech Stack
- **Python 3**  
- **Pygame**  
- **SQLite** (word + player database)  
- **NLTK** (word dataset source)  
- **pyttsx3** (offline text-to-speech)  
- **PyInstaller** (for EXE build)

---

## 🧩 How to Download & Play

### ✔ 1. Clone the repository
```bash
git clone https://github.com/<your-username>/Spelloverse.git
cd Spelloverse
```

### ✔ 2. Create a virtual environment (optional but recommended)
```bash
python -m venv venv
venv\Scripts\activate
```

### ✔ 3. Install dependencies
```bash
pip install -r requirements.txt
```

### ✔ 4. Run the game
```bash
python main.py
```

The game will automatically:
- Generate the word dataset (only on first run)
- Load both modes
- Display UI & menus correctly


## Build EXE
If you want to build an EXE yourself:

```bash
pyinstaller --noconsole --windowed ^
--icon "game_icon.ico" ^
--exclude-module PyQt5 ^
--exclude-module PyQt6 ^
--exclude-module PySide2 ^
--exclude-module PySide6 ^
--add-data "assets;assets" ^
--add-data "systems;systems" ^
--add-data "modes;modes" ^
--add-data "data;data" ^
main.py
```

This produces:
```bash
dist/main/main.exe
```
---

## 🗂 Folder Structure
```bash
SpelloVerse/
├── assets/ # images, bg, sfx
├── systems/ # db & audio utilities
├── modes/ # mode1.py, mode2.py
├── data/ # word dataset + sqlite db
├── dist/ # built exe output
├── game_icon.ico
├── main.py
└── README.md
```

---

## 🐞 Known Bugs (To Be Fixed)

### Mode 1  
- Rare double-trigger on chain matches  
- Very long meanings can overflow HUD  

### Mode 2  
- Fast diagonal dragging may skip tiles  
- No backtracking once a tile is selected  
- Glow blur grows on very long paths  
- Invalid-flash stacks if spammed  

### General  
- Dataset generation is slow on *first run*  
- Some icons may need to be replaced for better visual aesthetic and consistency
- Audio mixer may fail silently on some systems  
- HUD flickers slightly on match animations  

---

## 🌟 Planned Enhancements
- HD gem & tile icons  
- Animated starfield background  
- Smoother main menu transitions  
- Better SFX / ambient space music  
- Difficulty levels  
- Timed challenge modes  
- New mini-games  
- Achievements & badges  
- Daily quests  

---



