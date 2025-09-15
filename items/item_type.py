from dark_libraries.custom_decorators import auto_init, immutable

@immutable
@auto_init
class ItemType:
    item_id: int
    tile_id: int
    name: str
