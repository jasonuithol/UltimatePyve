from enum import Enum

from datetime import datetime, timedelta
from collections import deque

#
# rune font values for the celestial objects.
#
class CelestialGlyphCodes(Enum):
    SUN             = 42

    NEW_MOON        = 48
    CRESCENT_WAXING = 49
    HALF_WAXING     = 50
    GIBBIOUS_WAXING = 51

    FULL_MOON       = 52
    GIBBIOUS_WANING = 53
    HALF_WANING     = 54
    CRESCENT_WANING = 55

# WORLD CREATION TIME
#
# 8:35am on 4-5-139 (mm-dd-yyyy format - Britannian Daylight Savings Time)
#
# - Trammel is not visible.
# - Felucca is half waxing.
#
# at 3pm later that day, Trammel is gibbious waxing.
# at midnight that night, Trammel is gibbious waxing and Felucca is half waxing
#
# ========================= PHASE OFFSET CALCULATION INFORMATION ============================
# at 12:01am (one minute later): trammel goes full moon and Felucca goes gibbious waxing.
# ===========================================================================================
#
# Trammel period =  9 days = 216 hours.  Hence 1 phase shift per 27 hours.
# Felucca period = 14 days = 336 horus.  Hence 1 phase shift per 42 hours.
#
# ergo: at creation time (rounded down to 8:00am): Trammel is 16 hours behind a full moon, and Felucca is 16 hours behind half waxing.
# ergo: at creation time (rounded down to 8:00am): Trammel is 4 phases - 16 hours = 27 * 4 - 16 hours = 92 hours ahead of a new moon.
# and
# ergo: at creation time (rounded down to 8:00am): Felucca is 3 phases - 16 hours = 42 * 3 - 16 hours = 110 ahead of a new moon.
#
class Moon:
    def __init__(
        self, 
        name: str,
        synodic_period_days: int,
        phase_offset_hours: int,
    ):
        self.name = name
        self.synodic_period_days = synodic_period_days
        self.phase_length_hours = (synodic_period_days * 24) // 8 # there are 8 phases of any moon.
        self.phase_offset_hours = phase_offset_hours

    def get_moon_phase(self, clock: 'WorldClock') -> int:
        world_hours_elapsed = clock.get_turns_passed() // 60
        return (world_hours_elapsed + self.phase_offset_hours) // self.phase_length_hours


TRAMMEL = Moon(
    name = "Trammel", 
    synodic_period_days = 9,
    phase_offset_hours  = 92
)

FELUCCA = Moon(
    name = "Felucca", 
    synodic_period_days = 14,
    phase_offset_hours  = 110
)

WORLD_START_TIME = datetime(year=139, month=4, day=4, hour=8, minute=35)

class WorldClock:

    def _after_inject(self):
        self.turns_passed = 0
        self.set_world_time(WORLD_START_TIME)

    def pass_time(self):
        self.turns_passed +=1 
        self.world_time += timedelta(minutes=1)
        self.daylight_savings_time += timedelta(minutes=1)

    def set_world_time(self, dt: datetime):
        self.world_time = dt
        self.daylight_savings_time = dt + timedelta(hours = 1)

    def get_natural_time(self):
        return self.world_time
    
    def get_daylight_savings_time(self):
        return self.daylight_savings_time

    def get_turns_passed(self):
        return self.turns_passed

    # returns rune font codes.
    def get_celestial_panorama(self) -> list[int]:
        # There are 24 hours in a day, with 1 celestial turn per hour.
        # Ergo this panorama is 24 characters wide.

        sun  = CelestialGlyphCodes.SUN.value
        tram = CelestialGlyphCodes.NEW_MOON.value + TRAMMEL.get_moon_phase(self)
        felu = CelestialGlyphCodes.NEW_MOON.value + FELUCCA.get_moon_phase(self)

        # This represents midnight.  Imagine the ends are joined together in a circle, representing the celestial sphere.
        panorama = deque([
            0,0,0,    0,0,0,

            0,0,tram,   0,0,0,      # /---  these middle bits are 
            0,0,felu,   0,0,0,      # \---  the visible bits at midnight

            0,0,0,      0,0,sun,
        ])

        # rotate left the number of hours since midnight to get panorama at current hour.
        panorama.rotate(self.world_time.hour * -1)

        # Show only the "middle" 12 hours i.e. the side of the celestial sphere we are facing at the current hour.
        return list(panorama)[6:18]

    '''
    self.interactive_console.print_rune([42,48,49,50,51,52,53,54,55])

    ALL CELESTIAL MOVEMENTS HAPPEN ON THE HOUR

    1st moonrise 3:00pm
    sunset 6pm
    first dark 7:00pm   (4 corners)
                        another way to say that, a radius of light 6 squares NEWS and 5 squars diag
    2nd   dark 7:10pm   (3 squares each cnr)
                        another way to say that, a radius of light 5 squares NEWS and 4 squars diag
    3rd   dark 7:20pm   (one whole border, then 3 squares each cnr inside that)
                        another way to say that, a radius of light 3 squares NEWS and 3 squars diag
    4th   dark 7:30pm   (just a radius of light 3 squares NEWS, 2 squares diag)
    5th   dark 7:40pm   (2 squares NEWS, 1 squr diag)
    6th   dark 7:50pm   (total dark = 1 sqaure)
    2nd moonrise 9:00pm

    first light 5:10am
    2nd   light 5:20am  
    etcv
    sunrise 6:00am
    
    it is implied that maximum darkness is at 1am, which means that Britannia uses daylight saving or something.
    '''
    def _increments_from_1am(self):

        minutes_since_midnight = self.world_time.hour * 60 + self.world_time.minute
        # TODO: Explain the magic numbers a bit better.  They are not arbitrary.
        sawtooth = (72 - abs(72 - (minutes_since_midnight // 10))) - 36
        return sawtooth

    # There's no guarantee that there's a lightmap for every returned radius
    def get_current_light_radius(self) -> int:
        return self._increments_from_1am()
