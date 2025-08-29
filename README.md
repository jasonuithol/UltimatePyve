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
   ```
   git clone https://github.com/jasonuithol/UltimatePyve.git
   cd UltimatePyve
   ```

## Monkeypatching

    Right now - you'll need to copy your Ultima V directory to a folder under UltimatePyve and name that copy of Ultima v directory "u5"

    e.g.

    UltimatePyve
    |
    \- loaders
    \- u5

    I hope to get rid of this requirement later but for now, it is what it is.

### IMPORTANT REASSURANCE: This program does NOT alter your u5 or Ultima V directory or file contents.

## Running

    Running the main engine:
    ```
    python main.py
    ```

    Running diagnostic/test scripts:

    ```
    rem
    rem Any/All of these.
    rem

   
    ```

---

## Legal
    
    This project does not include any copyrighted game data.
    You must supply your own legal copy of Ultima V: Warriors of Destiny.
    
## Notes

    - This engine is designed to be fully compatible with the original PC data files.
    - It’s also built with modding and debugging in mind — you can extend maps, add triggers, or inspect raw data without touching the original files

## Acknowledgements

    - https://wiki.ultimacodex.com the source of much wisdom especially around file formats.
    - ChatGPT5 - thanks buddy.

