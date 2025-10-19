import pygame

from object_viewer_lib.object_viewer_profiles import ViewerProfile

class ObjectViewerMenuBar:

    def __init__(self, profiles: list[ViewerProfile], font: pygame.font.Font, height: int = 30):

        self.profiles = profiles
        self.font     = font
        self.height   = height
        self.buttons  = list[tuple[ViewerProfile, pygame.Surface, pygame.Rect]]()

        x = 0

        for profile in profiles:
            text_surf = font.render(profile.dropdown_label, True, (255,255,255))
            rect = text_surf.get_rect(topleft=(x, 0))
            rect.w += 20  # padding
            self.buttons.append((profile, text_surf, rect))
            x += rect.w
        self.active = profiles[0]

    def draw(self, surface: pygame.Surface):
        for profile, text_surf, rect in self.buttons:
            color = (80,80,80) if profile == self.active else (40,40,40)
            pygame.draw.rect(surface, color, rect)
            surface.blit(text_surf, rect.topleft)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for profile, _, rect in self.buttons:
                if rect.collidepoint(event.pos):
                    self.active = profile
                    self.active.initialise_components()