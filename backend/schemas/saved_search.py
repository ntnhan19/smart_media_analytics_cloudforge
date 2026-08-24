from pydantic import BaseModel
from datetime import datetime

class SavedSearchBase(BaseModel):
    query_text: str

class SavedSearchCreate(SavedSearchBase):
    pass

class SavedSearchResponse(SavedSearchBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
