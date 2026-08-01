from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON


class StaffMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: str = Field(index=True)
    discord_id: str = Field(index=True)
    username: str
    discriminator: Optional[str] = None
    avatar_url: Optional[str] = None
    category: Optional[str] = None
    role_names: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    badges: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    status: str = Field(default='offline')
    joined_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None


class StaffStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    member_id: int = Field(foreign_key='staffmember.id', index=True)
    voice_minutes: int = Field(default=0)
    tickets_handled: int = Field(default=0)
    moderation_actions: int = Field(default=0)
    warns: int = Field(default=0)
    messages_sent: int = Field(default=0)
    xp: int = Field(default=0)
    level: int = Field(default=1)
    ratings_total: int = Field(default=0)
    ratings_count: int = Field(default=0)

    @property
    def average_rating(self) -> float:
        if self.ratings_count == 0:
            return 0.0
        return round(self.ratings_total / self.ratings_count, 2)


class StaffNotificationSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: str = Field(index=True, unique=True)
    channel_id: Optional[str] = Field(default=None)
    enabled: bool = Field(default=True)
    staff_role_ids: list[int] = Field(sa_column=Column(JSON), default_factory=list)
    announce_entry: bool = Field(default=True)
    announce_exit: bool = Field(default=True)
    announce_promotion: bool = Field(default=True)
    announce_demotion: bool = Field(default=True)
    announce_role_add: bool = Field(default=True)
    announce_role_remove: bool = Field(default=True)


class StaffEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: str = Field(index=True)
    user_id: str
    username: Optional[str] = Field(default=None)
    discriminator: Optional[str] = Field(default=None)
    event_type: str
    old_role_ids: list[int] = Field(sa_column=Column(JSON), default_factory=list)
    old_role_names: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    new_role_ids: list[int] = Field(sa_column=Column(JSON), default_factory=list)
    new_role_names: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    actor_id: Optional[str] = Field(default=None)
    actor_name: Optional[str] = Field(default=None)
    channel_id: Optional[str] = Field(default=None)
    event_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
