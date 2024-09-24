from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional, Union, Dict

class ArtistCreate(BaseModel):
    name: str = Field(..., example="Artist Name")

class Artist(BaseModel):
    id: int
    name: str

class AlbumCreate(BaseModel):
    artist_name: str
    name: str
    release_date: str
    price: float

    @field_validator('release_date')
    def validate_release_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('release_date must be in YYYY-MM-DD format')

class AlbumInfo(BaseModel):
    id: int
    name: str
    release_date: str
    price: float
    average_rating: float

class AlbumWithArtist(BaseModel):
    id: int
    artist_id: int
    artist_name: str
    name: str
    release_date: str
    price: float
    average_rating: float

class ArtistDetail(BaseModel):
    id: int
    name: str
    albums: List[AlbumInfo]

class RatingCreate(BaseModel):
    album_name: str
    rating: int

    @field_validator('rating')
    def validate_rating(cls, v):
        if not (1 <= v <= 5):
            raise ValueError('Rating must be between 1 and 5.')
        return v

class RatingResponse(BaseModel):
    album_id: int
    average_rating: float
