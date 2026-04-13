from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class RegistrationModeEnum(str, Enum):
    none = "none"
    internal = "internal"
    external = "external"


class EventDateIn(BaseModel):
    event_date: date


class EventCreate(BaseModel):
    title: str = Field(..., max_length=512)
    sort_order: int = 0
    archived: bool = False
    registration_mode: RegistrationModeEnum
    external_url: str | None = None
    description_html: str = ""
    reminder_enabled: bool = False
    reminder_snippet_html: str | None = None
    dates: list[date] = []


class EventUpdate(BaseModel):
    title: str | None = Field(None, max_length=512)
    sort_order: int | None = None
    archived: bool | None = None
    registration_mode: RegistrationModeEnum | None = None
    external_url: str | None = None
    description_html: str | None = None
    reminder_enabled: bool | None = None
    reminder_snippet_html: str | None = None
    dates: list[date] | None = None


class EventOut(BaseModel):
    id: int
    title: str
    sort_order: int
    archived: bool
    registration_mode: RegistrationModeEnum
    external_url: str | None = None
    description_html: str
    reminder_enabled: bool
    reminder_snippet_html: str | None = None
    dates: list[date]

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class RegistrationOut(BaseModel):
    id: int
    user_id: int
    username: str | None
    event_id: int
    event_title: str
    name: str
    contact: str
    reg_code: str
    registered_at: datetime

    model_config = {"from_attributes": True}


class RegistrationListOut(BaseModel):
    items: list[RegistrationOut]
    total: int
    distinct_users: int
    distinct_events: int
    limit: int
    offset: int


class AppSettingsOut(BaseModel):
    reminder_hour_msk: int
    schedule_caption: str
    schedule_image_path: str
    schedule_missing_message: str
    admin_brand_title: str

    model_config = {"from_attributes": True}


class AppSettingsUpdate(BaseModel):
    reminder_hour_msk: int | None = Field(None, ge=0, le=23)
    schedule_caption: str | None = Field(None, max_length=4096)
    schedule_image_path: str | None = Field(None, max_length=1024)
    schedule_missing_message: str | None = Field(None, max_length=4096)
    admin_brand_title: str | None = Field(None, max_length=256)

    @field_validator(
        "schedule_caption",
        "schedule_image_path",
        "schedule_missing_message",
        "admin_brand_title",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            return v.strip()
        return v


class AnalyticsSummary(BaseModel):
    total_registrations: int
    unique_users: int
    unique_names: int
    by_event: list[dict]
    by_day: list[dict]
    new_users_by_day: list[dict]
