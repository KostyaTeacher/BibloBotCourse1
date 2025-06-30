from pydantic import BaseModel

class Book(BaseModel):
    name: str
    description: str
    rating: float
    genre: str
    authors: list[str]
    poster: str