from dark_libraries.service_provider import ServiceProvider

import controllers.service_composition
import data.service_composition
import models.service_composition
import services.service_composition
import view.service_composition

def compose(provider: ServiceProvider):

    for module in [controllers, data, models, services, view]:
        print(f"(root compose) Pre-registering {module.__name__.upper()}")
        module.service_composition.compose(provider)

    print("(root compose) Pre-registration COMPLETE")
    