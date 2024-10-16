from typing import Optional

from pydantic import BaseModel


class TelethonUserSchema(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    number: Optional[str] = None
    proxy: Optional[dict] = None
    active: Optional[bool] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class TelethonParserChannelSchema(BaseModel):
    id: Optional[int] = None
    link: Optional[str] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class TelethonUserWithChannelAssociationlSchema(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    parser_channel_id: Optional[int] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


# PayloadSchemas
class AddChannelSchema(BaseModel):
    user_id: Optional[int] = None
    parser_id: Optional[int] = None
    parser_link: Optional[str] = None
