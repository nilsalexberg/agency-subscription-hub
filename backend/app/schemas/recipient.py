from datetime import datetime

from pydantic import BaseModel


class RecipientRead(BaseModel):
    id: int
    name: str
    document: str
    efi_recipient_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecipientWrite(BaseModel):
    name: str
    document: str
    efi_recipient_id: str | None = None
