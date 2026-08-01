from ..base import ModuleBase
from .. import register_module
from .models import StaffMember, StaffStats, StaffNotificationSettings, StaffEvent
from .schemas import StaffMemberCreate, StaffMemberUpdate, StaffMemberRead
from .service import StaffService


@register_module
class StaffModule(ModuleBase):
    name = 'staff'
    title = 'Staff'
    model = StaffMember
    schema_create = StaffMemberCreate
    schema_update = StaffMemberUpdate
    schema_read = StaffMemberRead

    @classmethod
    def get_service(cls):
        return StaffService()

    @classmethod
    def get_models(cls) -> list:
        return [cls.model, StaffStats, StaffNotificationSettings, StaffEvent]

    @classmethod
    def get_router(cls):
        from .router import router as staff_router
        return staff_router

    @classmethod
    def get_ui_router(cls):
        from .router import ui_router
        return ui_router

    @classmethod
    def get_templates_dir(cls):
        from pathlib import Path
        from importlib import import_module
        mod = import_module(cls.__module__)
        return Path(mod.__file__).resolve().parent / 'templates'

    @classmethod
    def get_static_dir(cls):
        from pathlib import Path
        from importlib import import_module
        mod = import_module(cls.__module__)
        return Path(mod.__file__).resolve().parent / 'static'
