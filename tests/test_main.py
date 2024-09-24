import sys
import os

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
import sqlite3

DATABASE = 'test_music_catalog.db'

def override_get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

app.dependency_overrides[get_db] = override_get_db

class MusicCatalogTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use a separate database for testing
        if os.path.exists(DATABASE):
            os.remove(DATABASE)
        conn = sqlite3.connect(DATABASE)
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        conn.close()

    def setUp(self):
        self.client = TestClient(app)
        # Clear data from tables before each test
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM ratings')
        cursor.execute('DELETE FROM albums')
        cursor.execute('DELETE FROM artists')
        conn.commit()
        conn.close()

    def test_create_artist(self):
        artist_name = 'Artist for Create Artist Test'
        response = self.client.post('/artists', json={'name': artist_name})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['name'], artist_name)

    def test_create_album(self):
        # First, create an artist
        artist_name = 'Artist for Create Album Test'
        self.client.post('/artists', json={'name': artist_name})

        # Then, create an album for that artist
        album_name = 'Album for Create Album Test'
        album_response = self.client.post('/albums', json={
            'artist_name': artist_name,
            'name': album_name,
            'release_date': '2023-10-01',
            'price': 9.99
        })
        self.assertEqual(album_response.status_code, 201)
        album_data = album_response.json()
        self.assertEqual(album_data['name'], album_name)
        self.assertEqual(album_data['artist_name'], artist_name)

    def test_submit_rating(self):
        # Create artist and album first
        artist_name = 'Artist for Rating Test'
        album_name = 'Album for Rating Test'
        self.client.post('/artists', json={'name': artist_name})

        self.client.post('/albums', json={
            'artist_name': artist_name,
            'name': album_name,
            'release_date': '2015-08-28',
            'price': 20.0
        })

        # Submit rating using album_name
        rating_response = self.client.post('/albums/ratings', json={
            'album_name': album_name,
            'rating': 5
        })
        self.assertEqual(rating_response.status_code, 201)
        rating_data = rating_response.json()
        self.assertEqual(rating_data['average_rating'], 5.0)

    def test_search_artist(self):
        # Create artist and album
        artist_name = 'Artist for Search Test'
        album_name = 'Album for Search Test'
        self.client.post('/artists', json={'name': artist_name})

        self.client.post('/albums', json={
            'artist_name': artist_name,
            'name': album_name,
            'release_date': '2020-03-20',
            'price': 15.0
        })

        # Search for the artist
        search_response = self.client.get(f'/search?q={artist_name}')
        self.assertEqual(search_response.status_code, 200)
        search_data = search_response.json()
        self.assertIn('id', search_data)
        self.assertEqual(search_data['name'], artist_name)
        self.assertIsInstance(search_data['albums'], list)
        self.assertGreaterEqual(len(search_data['albums']), 1)
        album_names = [album['name'] for album in search_data['albums']]
        self.assertIn(album_name, album_names)

    def test_search_album(self):
        # Create artist and album
        artist_name = 'Artist for Album Search Test'
        album_name = 'Album for Album Search Test'
        self.client.post('/artists', json={'name': artist_name})

        self.client.post('/albums', json={
            'artist_name': artist_name,
            'name': album_name,
            'release_date': '2015-11-20',
            'price': 14.99
        })

        # Search for the album
        search_response = self.client.get(f'/search?q={album_name}')
        self.assertEqual(search_response.status_code, 200)
        search_data = search_response.json()
        self.assertIn('albums', search_data)
        self.assertIsInstance(search_data['albums'], list)
        self.assertGreaterEqual(len(search_data['albums']), 1)
        self.assertEqual(search_data['albums'][0]['name'], album_name)
        self.assertEqual(search_data['albums'][0]['artist_name'], artist_name)

    def test_search_no_results(self):
        # Search for a non-existing artist/album
        search_response = self.client.get('/search?q=NonExisting')
        self.assertEqual(search_response.status_code, 200)
        search_data = search_response.json()
        self.assertEqual(search_data, {})

    def test_submit_rating_multiple_albums(self):
        # Create multiple albums with the same name
        artist_name1 = 'Artist One for Rating Test'
        artist_name2 = 'Artist Two for Rating Test'
        album_name = 'Shared Album Name for Rating Test'

        self.client.post('/artists', json={'name': artist_name1})
        self.client.post('/artists', json={'name': artist_name2})

        self.client.post('/albums', json={
            'artist_name': artist_name1,
            'name': album_name,
            'release_date': '2021-01-01',
            'price': 10.0
        })

        self.client.post('/albums', json={
            'artist_name': artist_name2,
            'name': album_name,
            'release_date': '2021-02-01',
            'price': 12.0
        })

        # Try submitting a rating using the album name only
        rating_response = self.client.post('/albums/ratings', json={
            'album_name': album_name,
            'rating': 4
        })
        self.assertEqual(rating_response.status_code, 400)
        error_detail = rating_response.json()['detail']
        self.assertIn('Multiple albums found', error_detail)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(DATABASE):
            os.remove(DATABASE)

if __name__ == '__main__':
    unittest.main()
