# file: display/display_engine.py
import pygame

from dark_libraries.logging   import LoggerMixin

from services.view_port_service import ViewPortService
from view.display_config      import DisplayConfig
from view.info_panel          import InfoPanel
from view.interactive_console import InteractiveConsole
from view.view_port           import ViewPort
from view.main_display        import MainDisplay

from .view_port_data_provider import ViewPortDataProvider

class DisplayService(LoggerMixin):

    # Injectable
    display_config:      DisplayConfig

    main_display:        MainDisplay
    info_panel:          InfoPanel
    view_port:           ViewPort
    interactive_console: InteractiveConsole
    view_port_service:   ViewPortService

    #
    # TODO: Think about a view_port_service.
    #
    view_port_data_provider: ViewPortDataProvider

    def init(self):

        self.screen = pygame.display.set_mode(
            size  = self.main_display.scaled_size().to_tuple(),
            flags = pygame.SCALED | pygame.DOUBLEBUF, 
            vsync = 1
        )
        self.clock = pygame.time.Clock()
        self.set_window_title("Initialising....")

        self.log(f"Initialised {__class__.__name__}(id={hex(id(self))})")

    def get_fps(self):
        return self.clock.get_fps()

    def set_window_title(self, window_title: str):
        self._window_title = window_title

    def render(self):

        #
        # Window Title
        #
        pygame.display.set_caption(self._window_title + f", fps={self.clock.get_fps()}")

        scaled_border_thiccness = self.display_config.FONT_SIZE.w * self.display_config.SCALE_FACTOR

        #
        # Main Display
        #
        self.main_display.draw()
        md_scaled_surface = self.main_display.get_output_surface()
        md_scaled_pixel_offset = (0,0)
        self.screen.blit(md_scaled_surface, md_scaled_pixel_offset)

        #
        # ViewPort
        #

        # Render current viewport from populated map data.
        self.view_port_service.render()

        vp_scaled_surface = self.view_port.get_output_surface()
        vp_scaled_pixel_offset = (scaled_border_thiccness, scaled_border_thiccness)
        self.screen.blit(vp_scaled_surface, vp_scaled_pixel_offset)

        # Get ready to render all the stuff to the right of view_port
        right_hand_element_x = vp_scaled_surface.get_width() + scaled_border_thiccness * 2

        #
        # InfoPanel
        #
        self.info_panel.draw()

        ip_scaled_surface = self.info_panel.get_output_surface()
        ip_scaled_pixel_offset = (
            right_hand_element_x, 
            0
        )
        self.screen.blit(ip_scaled_surface, ip_scaled_pixel_offset)


        #
        # InteractiveConsole
        #
        self.interactive_console.draw()

        ic_scaled_surface = self.interactive_console.get_output_surface()
        ic_scaled_pixel_offset = (
            right_hand_element_x, 
            self.main_display.scaled_size().h - self.interactive_console.scaled_size().h - scaled_border_thiccness
        )
        self.screen.blit(ic_scaled_surface, ic_scaled_pixel_offset)

        pygame.display.flip()

        # allow reporting of FPS
        self.clock.tick()
