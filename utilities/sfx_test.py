import numpy as np, pygame

pygame.mixer.init(frequency=44100, size=-16, channels=2)
sr = 44100
t = np.linspace(0, 0.5, int(sr*0.5), endpoint=False)
wave = np.sin(2*np.pi*440*t) * 32767
stereo = np.column_stack((wave, wave)).astype(np.int16)
sound = pygame.sndarray.make_sound(stereo)
sound.play()
pygame.time.wait(600)

from gensound.signals import WhiteNoise
from gensound import Sine, ADSR

# A sine thump with ADSR envelope
thump = ADSR(attack=0.01, decay=0.5, sustain=0, release=0.5)(Sine(60))

# Broadband noise burst with ADSR envelope
hiss = ADSR(attack=0.005, decay=1.0, sustain=0, release=0.5)(WhiteNoise())


boom = thump + hiss
