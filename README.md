# Ultima V Engine – Drop‑In Replacement

This project is a **drop‑in replacement** for the original *Ultima V: Warriors of Destiny* PC engine.  
It uses the original game data files but runs them through a modern, Python‑based engine for easier modding, debugging, and expansion.

---

## Requirements

- This has been tested on Windows 10, Windows 11 and MacOS.

- **A legal copy of the PC version of Ultima V**  
  You can purchase a DRM‑free copy from [GOG.com](https://www.gog.com/en/game/ultima_4_5_6). This will be the PC version, but with this engine, you can run it on MacOS.  NOTE: It comes packaged in DOSBox - there's probably a way to run OG Ultima from GOG on MacOS.

  (I tried to find Ultima V on the appstore and could not.)

- **Python 3.13 or newer**  
  [Download Python here](https://www.python.org/downloads/).

---

## Installation

1. **Install Python 3.13+**  

    Make sure `pypi` points to the correct version (if that's even a thing).  When it asks if you want to add it to the PATH, say yes.


2. **Clone this repository**  

    ```
    git clone https://github.com/jasonuithol/UltimatePyve.git
    ```

    OR

    Download this link https://github.com/jasonuithol/UltimatePyve/archive/refs/heads/master.zip
    
    Unzip it and rename UltimatePyve-master to UltimatePyve


# IMPORTANT REASSURANCE: This program does NOT alter your u5 or Ultima V directory or file contents.

Currently, this program looks for your Ultima V installation at:

```
%ProgramFiles(x86)%\GOG Galaxy\Games\Ultima 5
```

and on MacOS it will find it at

```
/Applications/Ultima V™.app/Contents/Resources/game
```


These values live in configure.py

## Running

Double-click on **UltimatePyve.cmd**

## Updating

Double-click on **update.cmd** (Windows 10 onwards - for earlier versions, [install curl](https://curl.se/download.html) and add it to the system PATH)

## Legal
    
This project does not include any copyrighted game data.

You must supply your own legal copy of Ultima V: Warriors of Destiny.
    
## Notes

- This engine is designed to be fully compatible with the original PC data files.
- It’s also built with modding and debugging in mind — you will once again soon be able to extend maps, add triggers, or inspect raw data without touching the original files

## Acknowledgements

- https://wiki.ultimacodex.com the source of much wisdom especially around file formats, 
  and various other stats and data.
- ChatGPT5 - for fearlessness in the face of custom file formats, sound processing algorithms 
  and deep knowledge of python and pygame.
- Origin - for making the best computer game of 1987.
