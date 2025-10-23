#!/usr/bin/env python3
import msvcrt
import sys
import numpy as np
import pygame

SAMPLE_RATE = 44100
AMPLITUDE   = 32767

def make_wave(hz, sec):
    n_samples = int(SAMPLE_RATE * sec)
    if hz <= 0.0:
        return np.zeros((n_samples,), dtype=np.int16)
    t = np.arange(n_samples) / SAMPLE_RATE
    wave = 0.3 * np.sign(np.sin(2 * np.pi * hz * t))  # square wave
    return (wave * AMPLITUDE).astype(np.int16)

def play_sequence(seq):
    audio = np.concatenate([make_wave(hz, sec) for hz, sec in seq])
    # duplicate to stereo if mixer is stereo
    if pygame.mixer.get_init()[2] == 2:
        audio = np.column_stack((audio, audio))
    sound = pygame.sndarray.make_sound(audio)
    sound.play()
    pygame.time.wait(int(len(audio) / SAMPLE_RATE * 1000))

def read_sequences_from_stdin():
    sequences, current = [], []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if line.startswith("---"):
            if current:
                sequences.append(current)
                current = []
        else:
            hz, sec = map(float, line.split(","))
            current.append((hz, sec))
    if current:
        sequences.append(current)
    return sequences

if __name__ == "__main__":
    pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
    sequences = read_sequences_from_stdin()
    for i, seq in enumerate(sequences):
        print(f"Playing sequence {i} ({len(seq)} notes)")
        play_sequence(seq)
        print("Press any key for next...")
        # EVIL: Windows only
        msvcrt.getch()

    pygame.mixer.quit()