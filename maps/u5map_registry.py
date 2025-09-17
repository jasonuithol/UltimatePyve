from maps.u5map import U5Map

class U5MapRegistry:

    def _after_inject(self):
        self.u5maps: dict[int, U5Map] = {}
        self.u5maps_by_trigger_index: dict[int, U5Map] = {}
    
    def register_map(self, u5map: U5Map):
        self.u5maps[u5map.location_metadata.location_index] = u5map
        if not u5map.location_metadata.trigger_index is None:
            self.u5maps_by_trigger_index[u5map.location_metadata.trigger_index] = u5map

    def get_map(self, location_index: int):
        return self.u5maps[location_index]

    def get_map_by_trigger_index(self, trigger_index: int):
        return self.u5maps_by_trigger_index[trigger_index]
    