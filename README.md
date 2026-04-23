# Ultima V Engine – Drop‑In Replacement

This project is a **drop‑in replacement** for the original *Ultima V: Warriors of Destiny* PC engine.  
It uses the original game data files but runs them through a modern, Python‑based engine for easier modding, debugging, and expansion.

---

## Requirements

- This has been tested on Windows 10, Windows 11, MacOS

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


# IMPORTANT REASSURANCE: This program does NOT alter your Ultima V directory or file contents.

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

## Running on Linux

### UltimatePyve

I got this running on Linux !  the ```run.sh``` script will guide you through the setup process and will automatically take care of running the game.

You might need to copy the Ultima 5 files into a folder called ```u5``` under the UltimatePyve install directory.

### Original Ultimate V (GOG edition)

Despite GOG not offering a Linux download for Ultima V, it's actually trivial to set up the "Windows" version to run on Linux, because "Ultimately" it's just a DOSBox application...

You'll need DOSBox for linux.  On debian derived systems, installation is just:

```sudo apt install dosbox```

Then make a script inside the original Ultima 5 install directory (call it u5.sh):

```
#!/bin/bash
cd "$(dirname "$0")/DOSBOX"
dosbox -conf ../dosboxULTIMA5.conf -conf ../dosboxULTIMA5_single.conf -noconsole -c "exit"
```

Once created, give it execute permission:

```chmod u+x u5.sh```

Then run it !

```./u5.sh```

You'll see that it "fails" to load sound devices - that's fine, it'll fall back to the basic PC speaker sound effects.  Have fun !


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
