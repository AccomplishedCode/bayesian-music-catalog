import sqlite3
from .schemas import (
    ArtistCreate, Artist, AlbumCreate, AlbumWithArtist, AlbumInfo,
    ArtistDetail, RatingCreate, RatingResponse
)
from typing import List, Optional, Union, Dict

def create_artist(db: sqlite3.Connection, artist: ArtistCreate) -> Artist:
    cursor = db.execute('INSERT INTO artists (name) VALUES (?)', (artist.name,))
    db.commit()
    artist_id = cursor.lastrowid
    return Artist(id=artist_id, name=artist.name)

def create_album(db: sqlite3.Connection, album: AlbumCreate) -> Optional[AlbumWithArtist]:
    # Find the artist by name (case-insensitive)
    artist = db.execute(
        'SELECT * FROM artists WHERE LOWER(name) = LOWER(?)',
        (album.artist_name.lower(),)
    ).fetchone()
    if not artist:
        return None  # Artist not found

    artist_id = artist['id']
    cursor = db.execute(
        'INSERT INTO albums (artist_id, name, release_date, price) VALUES (?, ?, ?, ?)',
        (artist_id, album.name, album.release_date, album.price)
    )
    db.commit()
    album_id = cursor.lastrowid
    return AlbumWithArtist(
        id=album_id,
        artist_id=artist_id,
        artist_name=artist['name'],
        name=album.name,
        release_date=album.release_date,
        price=album.price,
        average_rating=0.0
    )

def get_artist_with_albums(db: sqlite3.Connection, artist_id: int) -> Optional[ArtistDetail]:
    artist = db.execute('SELECT * FROM artists WHERE id = ?', (artist_id,)).fetchone()
    if not artist:
        return None  # Artist not found

    albums = db.execute(
        'SELECT id, name, release_date, price, average_rating FROM albums WHERE artist_id = ? ORDER BY id',
        (artist_id,)
    ).fetchall()

    album_list = [AlbumInfo(**dict(album)) for album in albums]

    return ArtistDetail(
        id=artist['id'],
        name=artist['name'],
        albums=album_list
    )


def submit_rating(db: sqlite3.Connection, rating_data: RatingCreate) -> Optional[RatingResponse]:
    # Find the album by name (case-insensitive)
    albums = db.execute(
        'SELECT id FROM albums WHERE LOWER(name) = LOWER(?)',
        (rating_data.album_name.lower(),)
    ).fetchall()

    if not albums:
        return None  # Album not found

    if len(albums) > 1:
        # Multiple albums with the same name
        return 'multiple'  # Indicate multiple matches

    album_id = albums[0]['id']
    db.execute('INSERT INTO ratings (album_id, rating) VALUES (?, ?)', (album_id, rating_data.rating))
    db.commit()
    avg_rating = db.execute(
        'SELECT AVG(rating) as average_rating FROM ratings WHERE album_id = ?',
        (album_id,)
    ).fetchone()['average_rating']
    db.execute('UPDATE albums SET average_rating = ? WHERE id = ?', (avg_rating, album_id))
    db.commit()
    return RatingResponse(album_id=album_id, average_rating=avg_rating)

def search_artist_or_album(db: sqlite3.Connection, query: str) -> Optional[Union[ArtistDetail, Dict[str, List[AlbumWithArtist]]]]:
    # Try to find an artist matching the query
    artist_row = db.execute(
        'SELECT * FROM artists WHERE LOWER(name) = LOWER(?)',
        (query.lower(),)
    ).fetchone()

    if artist_row:
        # Artist found
        artist_id = artist_row['id']
        albums = db.execute(
            'SELECT id, name, release_date, price, average_rating FROM albums WHERE artist_id = ?',
            (artist_id,)
        ).fetchall()

        album_list = [AlbumInfo(**dict(album)) for album in albums]

        return ArtistDetail(
            id=artist_row['id'],
            name=artist_row['name'],
            albums=album_list
        )
    else:
        # Try to find albums matching the query
        albums = db.execute(
            """
            SELECT albums.id, albums.artist_id, albums.name, albums.release_date, albums.price, albums.average_rating, artists.name as artist_name
            FROM albums
            JOIN artists ON albums.artist_id = artists.id
            WHERE LOWER(albums.name) = LOWER(?)
            """,
            (query.lower(),)
        ).fetchall()

        if albums:
            album_list = [AlbumWithArtist(**dict(album)) for album in albums]
            return {'albums': album_list}
        else:
            # No matches found
            return None
