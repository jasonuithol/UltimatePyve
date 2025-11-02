# file: display/service_composition.py
from dark_libraries.service_provider import ServiceProvider
from models.agents.party_agent import PartyAgent
from models.party_inventory import PartyInventory

def compose(provider: ServiceProvider):
    provider.register_instance(PartyAgent())
    provider.register_instance(PartyInventory())
