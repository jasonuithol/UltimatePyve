import threading
from typing import Iterable
import pygame

from configure import get_u5_path

from dark_libraries.dark_math import Coord, Rect, Size, Vector2
from dark_libraries.service_provider import ServiceProvider

from data.global_registry import GlobalRegistry
from data.loaders.color_loader import ColorLoader
from data.loaders.projectile_sprite_loader import ProjectileSpriteLoader
from data.loaders.tileset_loader import TileLoader
from data.loaders.u5_font_loader import U5FontLoader
from data.loaders.u5_glyph_loader import U5GlyphLoader
from models.agents.party_agent import PartyAgent
from models.enums.ega_palette_values import EgaPaletteValues
from models.enums.projectile_type import ProjectileType
from models.tile import Tile
from models.u5_glyph import U5Glyph
from service_implementations.sound_service_implementation import SoundServiceImplementation
from service_implementations.surface_factory_implementation import SurfaceFactoryImplementation
from services.console_service import ConsoleService
from services.display_service import DisplayService
from services.input_service import InputService
from services.sfx_library_service import SfxLibraryService
from services.sound_service import SoundService
from services.surface_factory import SurfaceFactory
from services.view_port_data_provider import ViewPortData, ViewPortDataProvider
from services.view_port_service import ViewPortService
from view.display_config import DisplayConfig
from view.view_port import ViewPort

class ProgrammableInputService:

    def __init__(self):
        self.action_direction: Vector2[int] = None
        self.cursor_position: Coord[int]    = None
        self.next_event: pygame.event.Event = None

    def obtain_action_direction(self) -> Vector2[int]:
        return self.action_direction

    def obtain_cursor_position(self, starting_coord: Coord[int], boundary_rect: Rect[int], range_: int) -> Coord[int]:
        return self.cursor_position

    def get_next_event(self) -> pygame.event.Event:
        return self.next_event

    def discard_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

class DummyDisplayService:

    def _configure(self, screen: pygame.Surface, view_port: ViewPort, view_port_service: ViewPortService):
        self._screen = screen
        self._view_port = view_port
        self._view_port_service = view_port_service

    def init(self):
        pass
    def get_fps(self):
        return 9001
    def set_window_title(self, window_title: str):
        pass
    def render(self):
        self._view_port_service.render()
        screen.blit(self._view_port.get_output_surface(), (0,0))
        pygame.display.flip()

class DummyConsoleService:
    def print_ascii(self, msg: str | Iterable[int], include_carriage_return: bool = True, no_prompt = False):
        pass
    def print_runes(self, msg: str | Iterable[int], include_carriage_return: bool = True, no_prompt = False):
        pass
    def print_glyphs(self, glyphs: Iterable[U5Glyph], include_carriage_return: bool = True, no_prompt = False):
        pass

class ProgrammableViewPortDataProvider:

    def set_default_tile(self, tile: Tile):
        self.default_tile = tile
    def get_party_map_data(self, world_view_rect: Rect[int]) -> ViewPortData:
        return {
            coord : self.default_tile
            for coord in world_view_rect
        }
    def get_combat_map_data(self, world_view_rect: Rect[int]) -> ViewPortData:
        return {
            coord : self.default_tile
            for coord in world_view_rect
        }

#
# MAIN: Construct object graph.
#

provider = ServiceProvider()
sfx_library_service = SfxLibraryService()
provider.register_instance(sfx_library_service)

#
# SFX LIBRARY SERVICE Dependencies
#

provider.register(DisplayConfig)
provider.register(GlobalRegistry)

provider.register_mapping(InputService, ProgrammableInputService)
provider.register_mapping(SoundService, SoundServiceImplementation)
provider.register_mapping(DisplayService, DummyDisplayService)
provider.register(ViewPortService)
provider.register_mapping(ConsoleService, DummyConsoleService)

#
# VIEW PORT SERVICE Dependencies
#

party_agent = PartyAgent()
provider.register_instance(party_agent)
provider.register(ViewPort)
provider.register_mapping(ViewPortDataProvider, ProgrammableViewPortDataProvider)


#
# SCALABLE COMPONENT Dependencies
#

provider.register_mapping(SurfaceFactory, SurfaceFactoryImplementation)

#
# LOADERS
#

projectile_sprite_loader = ProjectileSpriteLoader()
u5_font_loader           = U5FontLoader()
u5_glyph_loader          = U5GlyphLoader()
color_loader             = ColorLoader()
tile_loader              = TileLoader()

provider.register_instance(projectile_sprite_loader)
provider.register_instance(u5_font_loader)
provider.register_instance(u5_glyph_loader)
provider.register_instance(color_loader)
provider.register_instance(tile_loader)

provider.inject_all()


#
# CONFIGURUATION
#

MAP_SIZE    = Size(11,11)
VIEW_SIZE    = Size(17,17)
MAP_RECT    = MAP_SIZE.to_rect(Coord[int](0,0))
TILE_SIZE   = Size(16,16)
SCALE_FACTOR = 2

START_COORD = Coord[int](5,9)
END_COORD   = Coord[int](5,2)
DIRECTION   = Vector2[int](0, -1)

PROJECTILE_TYPE = ProjectileType.MagicMissile
RAY_COLOR       = EgaPaletteValues.Magenta

#
# INTIIALISATION
#

pygame.init()
pygame.key.set_repeat(300, 50)  # Start repeating after 300ms, repeat every 50ms

screen = pygame.display.set_mode(
    size  = VIEW_SIZE * TILE_SIZE * SCALE_FACTOR,
    flags = pygame.SCALED | pygame.DOUBLEBUF, 
    vsync = 1
)
clock = pygame.time.Clock()

surface_factory: SurfaceFactory = provider.resolve(SurfaceFactory)
view_port: ViewPort = provider.resolve(ViewPort)
view_port_service: ViewPortService = provider.resolve(ViewPortService)
dummy_display_service: DummyDisplayService = provider.resolve(DisplayService)
view_port_data_provider: ProgrammableViewPortDataProvider = provider.resolve(ViewPortDataProvider)
sound_service: SoundService = provider.resolve(SoundService)

blank_tile = Tile(255, None, None)
blank_tile_surface = surface_factory.create_surface(TILE_SIZE * SCALE_FACTOR)
blank_tile_surface.fill((128,128,128))
blank_tile.set_surface(blank_tile_surface)
view_port_data_provider.set_default_tile(blank_tile)

dummy_display_service._configure(screen, view_port, view_port_service)

sound_service.init()

u5_path = get_u5_path()
u5_font_loader.register_fonts(u5_path)

color_loader.load()
u5_glyph_loader.register_glyphs()

projectile_sprite_loader.load()
tile_loader.load_tiles(u5_path)

view_port_service.set_combat_mode()


#
# Automatic method invoker
#

methods = [m for m in dir(sfx_library_service) if callable(getattr(sfx_library_service, m))]
public_methods = [m for m in methods if not m.startswith("_")]
print(public_methods)

current_method_index = 0

argument_dict = {
    "start_coord"     : START_COORD,
    "spell_direction" : DIRECTION,
    "color"           : RAY_COLOR,
    "ray_boundaries"  : MAP_RECT,
    "coord"           : END_COORD,
    "projectile_type" : ProjectileType.MagicMissile,
    "msg"             : "dummy log message",
    "start_world_coord" : START_COORD,
    "finish_world_coord" : END_COORD
}

import inspect

def call_with_dict(obj, method_name: str, arg_dict: dict[str, object]):
    func = getattr(obj, method_name)
    sig = inspect.signature(func)

    # Validate that your dict matches the signature
    try:
        bound = sig.bind_partial(**arg_dict)
        bound.apply_defaults()
    except TypeError as e:
        raise ValueError(f"Bad arguments for {method_name}: {e}")

    print("Executing effect")
    #
    # NOTE: This will do hang if sound_service.render isn't being called in the main thread
    #       ergo this must be called by a worker
    #
    thread = threading.Thread(
        target = func,
        kwargs = arg_dict
    )
    thread.start()
    while thread.is_alive():
        dummy_display_service.render()
        sound_service.render()
        clock.tick(60)   # prevent 100% CPU spin
        pygame.event.pump()


    print("Execution finished")

#
# MAIN LOOP
#

while True:
    pygame.display.set_caption(public_methods[current_method_index])
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                current_method_index = (current_method_index - 1) % len(public_methods)
            if event.key == pygame.K_RIGHT:
                current_method_index = (current_method_index + 1) % len(public_methods)
            if event.key == pygame.K_RETURN:

                func = getattr(sfx_library_service, public_methods[current_method_index])
                sig = inspect.signature(func)
                params = [p for p in sig.parameters.keys() if p != "self"]

                arguments = {
                    param_name : argument_dict[param_name]
                    for param_name in params
                }

                call_with_dict(sfx_library_service, public_methods[current_method_index], arguments)
                break # skipp the rest of the events

        pygame.display.set_caption(public_methods[current_method_index])

    dummy_display_service.render()
    sound_service.render()
    clock.tick(60)   # prevent 100% CPU spin
