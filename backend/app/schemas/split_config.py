from datetime import datetime

from pydantic import BaseModel


class SplitConfigRead(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SplitConfigWrite(BaseModel):
    name: str
