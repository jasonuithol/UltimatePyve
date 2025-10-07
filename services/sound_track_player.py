import pygame

class SoundTrackPlayer:

    def play(self, path):
        if path is None:
            return
        pygame.mixer.music.stop()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play(-1)

    def stop(self):
        pygame.mixer.music.stop()

    
        