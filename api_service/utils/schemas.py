from typing import Generic, TypeVar, Optional

from pydantic.generics import GenericModel

DataT = TypeVar('DataT')


class Response(GenericModel, Generic[DataT]):
    status: str
    data: Optional[DataT] = None
    details: Optional[str] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
