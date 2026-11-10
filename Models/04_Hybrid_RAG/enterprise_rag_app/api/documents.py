from pydantic import BaseModel

class DocumentMeta(BaseModel):
    id: str
    title: str
    category: str

