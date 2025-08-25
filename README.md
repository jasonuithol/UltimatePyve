# Ultima V Engine – Drop‑In Replacement

This project is a **drop‑in replacement** for the original *Ultima V: Warriors of Destiny* PC engine.  
It uses the original game data files but runs them through a modern, Python‑based engine for easier modding, debugging, and expansion.

---

## Requirements

- **A legal copy of the PC version of Ultima V**  
  You can purchase a DRM‑free copy from [GOG.com](https://www.gog.com/en/game/ultima_4_5_6).
- **Python 3.11 or newer**  
  [Download Python here](https://www.python.org/downloads/).

---

## Installation

1. **Install Python 3.11+**  
   Make sure `python` (or `python3`) points to the correct version.  When it asks if you want to add it to the PATH, say yes.

2. **Clone this repository**  
   ```bash
   git clone https://github.com/jasonuithol/UltimatePyve.git
   cd UltimatePyve

## Monkeypatching

    Right now - you'll need to copy your ultima V directory to a folder under UltimatePyve and name that ulimate v directory "u5"

    I hope to get rid of this requirement later but for now, it is what it is.

## Running

    There's not much right now, but you can run ```python viewer.py``` and roam around the over and under world (press TAB to switch)
    You can run ```python sprites.py``` to look at all the tiles in TILES.16
    Similarly ```python overworld.py``` and ```python underworld.py``` will generate full maps of these worlds.
    You can peek under the hood with ```python data.py``` to see all the various game-wide settings.
    
## Legal
    
    This project does not include any copyrighted game data.
    You must supply your own legal copy of Ultima V: Warriors of Destiny.
    
## Notes

    - This engine is designed to be fully compatible with the original PC data files.
    - It’s also built with modding and debugging in mind — you can extend maps, add triggers, or inspect raw data without touching the original files
