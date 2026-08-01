from ..base import ModuleBase
from .. import register_module
from .models import WelcomeConfig
from .schemas import WelcomeConfigCreate, WelcomeConfigUpdate, WelcomeConfigRead
from .service import WelcomeService


@register_module
class WelcomeModule(ModuleBase):
    name = 'welcome'
    title = 'Welcome'
    model = WelcomeConfig
    schema_create = WelcomeConfigCreate
    schema_update = WelcomeConfigUpdate
    schema_read = WelcomeConfigRead

    @classmethod
    def get_service(cls):
        return WelcomeService()
