from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class StaffStatsRead(BaseModel):
    voice_minutes: int = 0
    tickets_handled: int = 0
    moderation_actions: int = 0
    warns: int = 0
    messages_sent: int = 0
    xp: int = 0
    level: int = 1
    ratings_total: int = 0
    ratings_count: int = 0
    average_rating: float = 0.0


class StaffMemberBase(BaseModel):
    discord_id: str
    username: str
    discriminator: Optional[str] = None
    avatar_url: Optional[str] = None
    category: Optional[str] = None
    role_names: Optional[List[str]] = Field(default_factory=list)
    badges: Optional[List[str]] = Field(default_factory=list)
    status: Optional[str] = 'offline'
    joined_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None


class StaffMemberCreate(StaffMemberBase):
    pass


class StaffMemberUpdate(BaseModel):
    username: Optional[str] = None
    discriminator: Optional[str] = None
    avatar_url: Optional[str] = None
    category: Optional[str] = None
    role_names: Optional[List[str]] = None
    badges: Optional[List[str]] = None
    status: Optional[str] = None
    joined_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None


class StaffMemberRead(StaffMemberBase):
    id: int
    guild_id: str
    stats: StaffStatsRead = Field(default_factory=StaffStatsRead)

    class Config:
        orm_mode = True


class StaffOverviewRead(BaseModel):
    categories: dict[str, int] = Field(default_factory=dict)
    total_members: int = 0
    average_rating: float = 0.0
    total_tickets: int = 0
    total_moderation_actions: int = 0
    total_warns: int = 0
    total_messages: int = 0
    total_voice_minutes: int = 0


class StaffNotificationSettingsBase(BaseModel):
    channel_id: Optional[str] = None
    enabled: bool = True
    staff_role_ids: list[int] = Field(default_factory=list)
    announce_entry: bool = True
    announce_exit: bool = True
    announce_promotion: bool = True
    announce_demotion: bool = True
    announce_role_add: bool = True
    announce_role_remove: bool = True


class StaffNotificationSettingsCreate(StaffNotificationSettingsBase):
    pass


class StaffNotificationSettingsUpdate(StaffNotificationSettingsBase):
    pass


class StaffNotificationSettingsRead(StaffNotificationSettingsBase):
    id: int
    guild_id: str

    class Config:
        orm_mode = True


class StaffEventRead(BaseModel):
    id: int
    guild_id: str
    user_id: str
    username: Optional[str] = None
    discriminator: Optional[str] = None
    event_type: str
    old_role_ids: list[int] = Field(default_factory=list)
    old_role_names: list[str] = Field(default_factory=list)
    new_role_ids: list[int] = Field(default_factory=list)
    new_role_names: list[str] = Field(default_factory=list)
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    channel_id: Optional[str] = None
    event_message: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
