# file: display/service_composition.py
from dark_libraries.service_provider import ServiceProvider
from models.data_ovl import DataOVL
from models.party_inventory import PartyInventory
from models.party_state import PartyState

def compose(provider: ServiceProvider):
    provider.register_instance(DataOVL.load())
    provider.register_instance(PartyState())
    provider.register_instance(PartyInventory())
