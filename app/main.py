from fastapi import FastAPI, HTTPException, Depends
from typing import Union, Dict, List
from .schemas import (
    ArtistCreate, Artist, AlbumCreate, AlbumWithArtist, RatingCreate, RatingResponse,
    ArtistDetail
)
from .database import get_db
from .crud import (
    create_artist, create_album, submit_rating, search_artist_or_album
)
import sqlite3

app = FastAPI()

@app.post("/artists", response_model=Artist, status_code=201)
def api_create_artist(artist: ArtistCreate, db: sqlite3.Connection = Depends(get_db)):
    new_artist = create_artist(db, artist)
    return new_artist

@app.post("/albums", response_model=AlbumWithArtist, status_code=201)
def api_create_album(album: AlbumCreate, db: sqlite3.Connection = Depends(get_db)):
    album_result = create_album(db, album)
    if album_result is None:
        raise HTTPException(status_code=404, detail="Artist not found.")
    return album_result

@app.post("/albums/ratings", response_model=RatingResponse, status_code=201)
def api_submit_rating(rating_data: RatingCreate, db: sqlite3.Connection = Depends(get_db)):
    rating_result = submit_rating(db, rating_data)
    if rating_result is None:
        raise HTTPException(status_code=404, detail="Album not found.")
    elif rating_result == 'multiple':
        raise HTTPException(status_code=400, detail="Multiple albums found with that name. Please specify additional details.")
    return rating_result

@app.get("/search", response_model=Union[ArtistDetail, Dict[str, List[AlbumWithArtist]]])
def api_search(q: str = None, db: sqlite3.Connection = Depends(get_db)):
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter q is required.")

    result = search_artist_or_album(db, q)

    if result is None:
        return {}
    return result
