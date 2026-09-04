import os
import sys

# Force UTF-8 terminal encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import django
import urllib.request
from datetime import datetime, timedelta
from django.utils.text import slugify

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmyseat.settings')
django.setup()

from movies.models import Movie, Genre, Language, CastMember, Theater, Seat

print("--- Populating 52 Famous Movies (Safe Database Addition) ---")

MEDIA_DIR = os.path.join(os.path.dirname(__file__), 'media', 'movies')
os.makedirs(MEDIA_DIR, exist_ok=True)

MOVIES_DATA = [
    {
        "name": "Inception",
        "description": "A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
        "duration": 148,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=YoHD9XEInc0",
        "release": "2010-07-16",
        "rating": 4.8,
        "is_trending": True,
        "genres": ["Action", "Sci-Fi", "Thriller"],
        "languages": ["English"],
        "cast": [("Christopher Nolan", "Director"), ("Leonardo DiCaprio", "Lead Actor"), ("Joseph Gordon-Levitt", "Supporting Actor")],
        "poster_url": "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Oppenheimer",
        "description": "The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb.",
        "duration": 180,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=uYPbbksJxIg",
        "release": "2023-07-21",
        "rating": 4.9,
        "is_trending": True,
        "genres": ["Drama", "History", "Biography"],
        "languages": ["English", "Hindi"],
        "cast": [("Christopher Nolan", "Director"), ("Cillian Murphy", "Lead Actor"), ("Robert Downey Jr.", "Supporting Actor")],
        "poster_url": "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "The Dark Knight",
        "description": "When the menace known as the Joker wreaks havoc and chaos on Gotham, Batman must accept one of the greatest psychological tests.",
        "duration": 152,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=EXeTwQWrcwY",
        "release": "2008-07-18",
        "rating": 4.9,
        "is_trending": True,
        "genres": ["Action", "Crime", "Drama"],
        "languages": ["English", "Hindi"],
        "cast": [("Christopher Nolan", "Director"), ("Christian Bale", "Lead Actor"), ("Heath Ledger", "Supporting Actor")],
        "poster_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Interstellar",
        "description": "When Earth becomes uninhabitable, a team of ex-NASA pilots and researchers undertake a journey through a wormhole.",
        "duration": 169,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=zSWdZVtXT7E",
        "release": "2014-11-07",
        "rating": 4.8,
        "is_trending": True,
        "genres": ["Sci-Fi", "Adventure", "Drama"],
        "languages": ["English", "Hindi"],
        "cast": [("Christopher Nolan", "Director"), ("Matthew McConaughey", "Lead Actor"), ("Anne Hathaway", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Avatar: The Way of Water",
        "description": "Jake Sully lives with his newfound family on the extrasolar moon Pandora. When a familiar threat returns, Jake must work with Neytiri.",
        "duration": 192,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=d9MyW72ELq0",
        "release": "2022-12-16",
        "rating": 4.7,
        "is_trending": True,
        "genres": ["Sci-Fi", "Action", "Adventure"],
        "languages": ["English", "Hindi", "Tamil", "Telugu"],
        "cast": [("James Cameron", "Director"), ("Sam Worthington", "Lead Actor"), ("Zoe Saldana", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Avengers: Endgame",
        "description": "After devastating events, the universe is in ruins. With the help of remaining allies, the Avengers assemble once more to reverse Thanos.",
        "duration": 181,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=TcMBFSGVi1c",
        "release": "2019-04-26",
        "rating": 4.9,
        "is_trending": True,
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "languages": ["English", "Hindi", "Tamil", "Telugu"],
        "cast": [("Anthony Russo", "Director"), ("Robert Downey Jr.", "Lead Actor"), ("Chris Evans", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Titanic",
        "description": "A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the luxurious, ill-fated R.M.S. Titanic.",
        "duration": 194,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=kVrqfYjkTdQ",
        "release": "1997-12-19",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Drama", "Romance"],
        "languages": ["English", "Hindi"],
        "cast": [("James Cameron", "Director"), ("Leonardo DiCaprio", "Lead Actor"), ("Kate Winslet", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Spider-Man: Into the Spider-Verse",
        "description": "Teen Miles Morales becomes the Spider-Man of his universe and must join five spider-powered individuals from other dimensions.",
        "duration": 117,
        "age": "U",
        "trailer": "https://www.youtube.com/watch?v=g4Hbz2jLxvQ",
        "release": "2018-12-14",
        "rating": 4.8,
        "is_trending": True,
        "genres": ["Animation", "Action", "Adventure"],
        "languages": ["English", "Hindi"],
        "cast": [("Bob Persichetti", "Director"), ("Shameik Moore", "Lead Voice"), ("Hailee Steinfeld", "Lead Voice")],
        "poster_url": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Spider-Man: No Way Home",
        "description": "With Spider-Man's identity revealed, Peter asks Doctor Strange for help. When a spell goes wrong, dangerous foes from other worlds appear.",
        "duration": 148,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=JfVOs4VSpmA",
        "release": "2021-12-17",
        "rating": 4.8,
        "is_trending": True,
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "languages": ["English", "Hindi", "Tamil", "Telugu"],
        "cast": [("Jon Watts", "Director"), ("Tom Holland", "Lead Actor"), ("Zendaya", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1635805737707-575885ab0820?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "The Matrix",
        "description": "When a beautiful stranger leads computer hacker Neo to a forbidding underworld, he discovers the shocking truth about reality.",
        "duration": 136,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=vKQi3bBA1y8",
        "release": "1999-03-31",
        "rating": 4.7,
        "is_trending": False,
        "genres": ["Action", "Sci-Fi"],
        "languages": ["English", "Hindi"],
        "cast": [("Lana Wachowski", "Director"), ("Keanu Reeves", "Lead Actor"), ("Laurence Fishburne", "Supporting Actor")],
        "poster_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "RRR",
        "description": "A fictitious story about two legendary revolutionaries and their journey away from home before they started fighting for their country in the 1920s.",
        "duration": 187,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=NgBoT0NRH24",
        "release": "2022-03-25",
        "rating": 4.9,
        "is_trending": True,
        "genres": ["Action", "Drama", "History"],
        "languages": ["Telugu", "Hindi", "Tamil", "English"],
        "cast": [("S.S. Rajamouli", "Director"), ("N.T. Rama Rao Jr.", "Lead Actor"), ("Ram Charan", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Baahubali 2: The Conclusion",
        "description": "When Shiva, the son of Bahubali, learns about his heritage, he begins to look for answers. His story is juxtaposed with past events.",
        "duration": 167,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=qD-6d8Wo3do",
        "release": "2017-04-28",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Action", "Drama", "Fantasy"],
        "languages": ["Telugu", "Hindi", "Tamil"],
        "cast": [("S.S. Rajamouli", "Director"), ("Prabhas", "Lead Actor"), ("Rana Daggubati", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Dangal",
        "description": "Former wrestler Mahavir Singh Phogat and his two wrestler daughters struggle towards glory at the Commonwealth Games in the face of societal oppression.",
        "duration": 161,
        "age": "U",
        "trailer": "https://www.youtube.com/watch?v=x_7YlGv9u1g",
        "release": "2016-12-23",
        "rating": 4.9,
        "is_trending": False,
        "genres": ["Biography", "Drama", "Sport"],
        "languages": ["Hindi"],
        "cast": [("Nitesh Tiwari", "Director"), ("Aamir Khan", "Lead Actor"), ("Fatima Sana Shaikh", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "K.G.F: Chapter 2",
        "description": "In the blood-soaked Kolar Gold Fields, Rocky's name strikes fear into his foes. While his allies look up to him, the government sees him as a threat.",
        "duration": 168,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=JKa05nyUmuQ",
        "release": "2022-04-14",
        "rating": 4.8,
        "is_trending": True,
        "genres": ["Action", "Crime", "Drama"],
        "languages": ["Kannada", "Hindi", "Telugu", "Tamil"],
        "cast": [("Prashanth Neel", "Director"), ("Yash", "Lead Actor"), ("Sanjay Dutt", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Jawan",
        "description": "A high-octane action thriller which outlines the emotional journey of a man who is set to rectify the wrongs in the society.",
        "duration": 169,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=COv52Qyctws",
        "release": "2023-09-07",
        "rating": 4.7,
        "is_trending": True,
        "genres": ["Action", "Thriller"],
        "languages": ["Hindi", "Tamil", "Telugu"],
        "cast": [("Atlee", "Director"), ("Shah Rukh Khan", "Lead Actor"), ("Nayanthara", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Pathaan",
        "description": "An Indian agent races against time to stop a ruthless mercenary with a deadly plan against his homeland.",
        "duration": 146,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=vqu4z34wENw",
        "release": "2023-01-25",
        "rating": 4.6,
        "is_trending": True,
        "genres": ["Action", "Adventure", "Thriller"],
        "languages": ["Hindi", "Tamil", "Telugu"],
        "cast": [("Siddharth Anand", "Director"), ("Shah Rukh Khan", "Lead Actor"), ("Deepika Padukone", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "3 Idiots",
        "description": "Two friends are searching for their long lost companion. They revisit their college days and recall the memories of their friend who inspired them to think differently.",
        "duration": 170,
        "age": "U",
        "trailer": "https://www.youtube.com/watch?v=K0eDlFX9GMc",
        "release": "2009-12-25",
        "rating": 4.9,
        "is_trending": False,
        "genres": ["Comedy", "Drama"],
        "languages": ["Hindi"],
        "cast": [("Rajkumar Hirani", "Director"), ("Aamir Khan", "Lead Actor"), ("R. Madhavan", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Sholay",
        "description": "After his family is murdered by a notorious bandit, a former police officer enlists the help of two outlaws to capture him.",
        "duration": 204,
        "age": "U",
        "trailer": "https://www.youtube.com/watch?v=zzbfUjWj170",
        "release": "1975-08-15",
        "rating": 4.9,
        "is_trending": False,
        "genres": ["Action", "Adventure", "Comedy"],
        "languages": ["Hindi"],
        "cast": [("Ramesh Sippy", "Director"), ("Amitabh Bachchan", "Lead Actor"), ("Dharmendra", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Dilwale Dulhania Le Jayenge",
        "description": "When Raj & Simran meet on an inter-rail holiday in Europe, it isn't exactly love at first sight... but when Simran is taken back to India for an arranged marriage, things change.",
        "duration": 189,
        "age": "U",
        "trailer": "https://www.youtube.com/watch?v=c25GKl5Vn38",
        "release": "1995-10-20",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Drama", "Romance"],
        "languages": ["Hindi"],
        "cast": [("Aditya Chopra", "Director"), ("Shah Rukh Khan", "Lead Actor"), ("Kajol", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Lagaan: Once Upon a Time in India",
        "description": "The people of a small village in Victorian India stake their future on a game of cricket against their ruthless British rulers.",
        "duration": 224,
        "age": "U",
        "trailer": "https://www.youtube.com/watch?v=NqpR8a846c4",
        "release": "2001-06-15",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Drama", "Sport"],
        "languages": ["Hindi", "English"],
        "cast": [("Ashutosh Gowariker", "Director"), ("Aamir Khan", "Lead Actor"), ("Gracy Singh", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Gangs of Wasseypur",
        "description": "A clash between Sultan and Shahid Khan leads to the expulsion of Khan from Wasseypur, and ignites a deadly feud spanning three generations.",
        "duration": 320,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=j-AkWDkXcMY",
        "release": "2012-06-22",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Action", "Crime", "Drama"],
        "languages": ["Hindi"],
        "cast": [("Anurag Kashyap", "Director"), ("Manoj Bajpayee", "Lead Actor"), ("Nawazuddin Siddiqui", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Tumbbad",
        "description": "A mythological story about a goddess who created the entire universe. The plot revolves around the consequences of building a temple for her first-born monster Hastar.",
        "duration": 104,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=sN75heX59L0",
        "release": "2018-10-12",
        "rating": 4.9,
        "is_trending": True,
        "genres": ["Drama", "Fantasy", "Horror"],
        "languages": ["Hindi"],
        "cast": [("Rahi Anil Barve", "Director"), ("Sohum Shah", "Lead Actor"), ("Jyoti Malshe", "Supporting Actress")],
        "poster_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Stree",
        "description": "In the small town of Chanderi, the menfolk live in fear of an evil spirit named 'Stree' who abducts men in the night during festival days.",
        "duration": 128,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=gzeaGcLLl_A",
        "release": "2018-08-31",
        "rating": 4.7,
        "is_trending": False,
        "genres": ["Comedy", "Horror"],
        "languages": ["Hindi"],
        "cast": [("Amar Kaushik", "Director"), ("Rajkummar Rao", "Lead Actor"), ("Shraddha Kapoor", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Stree 2",
        "description": "The town of Chanderi is haunted once again, this time by a headless entity named 'Sarkata'. Vicky and his friends must unite to save their town.",
        "duration": 147,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=KVnheXywIbU",
        "release": "2024-08-15",
        "rating": 4.8,
        "is_trending": True,
        "genres": ["Comedy", "Horror"],
        "languages": ["Hindi"],
        "cast": [("Amar Kaushik", "Director"), ("Rajkummar Rao", "Lead Actor"), ("Shraddha Kapoor", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Drishyam",
        "description": "Desperate measures are taken by a man who tries to save his family from the dark side of the law, after they commit an unexpected crime.",
        "duration": 163,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=AuuX2j14NBg",
        "release": "2015-07-31",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Crime", "Drama", "Thriller"],
        "languages": ["Hindi"],
        "cast": [("Nishikant Kamat", "Director"), ("Ajay Devgn", "Lead Actor"), ("Tabu", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Kantara",
        "description": "When greed paves the way for a betrayal, a divine spirit takes over a human to settle the score in a rural coastal village.",
        "duration": 148,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=8mrVmf239GU",
        "release": "2022-09-30",
        "rating": 4.8,
        "is_trending": True,
        "genres": ["Action", "Adventure", "Drama"],
        "languages": ["Kannada", "Hindi", "Telugu", "Tamil"],
        "cast": [("Rishab Shetty", "Director"), ("Rishab Shetty", "Lead Actor"), ("Sapthami Gowda", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Animal",
        "description": "A fierce father-son bond unfolds against a backdrop of gang warfare and personal vengeance as a son vows revenge.",
        "duration": 201,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=Dydmpfo68DA",
        "release": "2023-12-01",
        "rating": 4.6,
        "is_trending": True,
        "genres": ["Action", "Crime", "Drama"],
        "languages": ["Hindi", "Telugu", "Tamil"],
        "cast": [("Sandeep Reddy Vanga", "Director"), ("Ranbir Kapoor", "Lead Actor"), ("Anil Kapoor", "Supporting Actor")],
        "poster_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Brahmastra: Part One - Shiva",
        "description": "A young man named Shiva discovers he has a mysterious connection to fire and holds the power to awaken the Astras.",
        "duration": 167,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=V5jVntRVlac",
        "release": "2022-09-09",
        "rating": 4.4,
        "is_trending": False,
        "genres": ["Action", "Adventure", "Fantasy"],
        "languages": ["Hindi", "Telugu", "Tamil"],
        "cast": [("Ayan Mukerji", "Director"), ("Ranbir Kapoor", "Lead Actor"), ("Alia Bhatt", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Dune: Part Two",
        "description": "Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family.",
        "duration": 166,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=Way9Dexny3w",
        "release": "2024-03-01",
        "rating": 4.9,
        "is_trending": True,
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "languages": ["English", "Hindi"],
        "cast": [("Denis Villeneuve", "Director"), ("Timothée Chalamet", "Lead Actor"), ("Zendaya", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Everything Everywhere All at Once",
        "description": "A middle-aged Chinese immigrant is swept up into an insane adventure in which she alone can save existence by exploring other universes.",
        "duration": 139,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=wxN1T1uxQ2g",
        "release": "2022-03-25",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Action", "Adventure", "Comedy"],
        "languages": ["English"],
        "cast": [("Daniel Kwan", "Director"), ("Michelle Yeoh", "Lead Actress"), ("Ke Huy Quan", "Supporting Actor")],
        "poster_url": "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "The Shawshank Redemption",
        "description": "Over the course of several years, two convicts form a friendship, seeking consolation and eventual redemption through basic compassion.",
        "duration": 142,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=6hB3S9bIaco",
        "release": "1994-10-14",
        "rating": 4.9,
        "is_trending": False,
        "genres": ["Drama"],
        "languages": ["English", "Hindi"],
        "cast": [("Frank Darabont", "Director"), ("Tim Robbins", "Lead Actor"), ("Morgan Freeman", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "The Godfather",
        "description": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant youngest son.",
        "duration": 175,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=sY1S348083Q",
        "release": "1972-03-24",
        "rating": 4.9,
        "is_trending": False,
        "genres": ["Crime", "Drama"],
        "languages": ["English", "Hindi"],
        "cast": [("Francis Ford Coppola", "Director"), ("Marlon Brando", "Lead Actor"), ("Al Pacino", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Pulp Fiction",
        "description": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
        "duration": 154,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=s7EdQ4FqbhY",
        "release": "1994-10-14",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Crime", "Drama"],
        "languages": ["English"],
        "cast": [("Quentin Tarantino", "Director"), ("John Travolta", "Lead Actor"), ("Samuel L. Jackson", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Fight Club",
        "description": "An insomniac office worker and a devil-may-care soap maker form an underground fight club that evolves into much more.",
        "duration": 139,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=qtRKDV93ujQ",
        "release": "1999-10-15",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Drama"],
        "languages": ["English", "Hindi"],
        "cast": [("David Fincher", "Director"), ("Brad Pitt", "Lead Actor"), ("Edward Norton", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Forrest Gump",
        "description": "The history of the United States from the 1950s to the '70s unfolds from the perspective of an Alabama man with an IQ of 75.",
        "duration": 142,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=bLvqoHBptjg",
        "release": "1994-07-06",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Drama", "Romance"],
        "languages": ["English", "Hindi"],
        "cast": [("Robert Zemeckis", "Director"), ("Tom Hanks", "Lead Actor"), ("Robin Wright", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Gladiator",
        "description": "A former Roman General sets out to exact vengeance against the corrupt emperor who murdered his family and sent him into slavery.",
        "duration": 155,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=P5ieIbInF5s",
        "release": "2000-05-05",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Action", "Adventure", "Drama"],
        "languages": ["English", "Hindi"],
        "cast": [("Ridley Scott", "Director"), ("Russell Crowe", "Lead Actor"), ("Joaquim Phoenix", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Gladiator II",
        "description": "Years after witnessing the death of Maximus at the hands of his uncle, Lucius must enter the Colosseum after his home is conquered.",
        "duration": 148,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=4mgB8V0XnJk",
        "release": "2024-11-22",
        "rating": 4.7,
        "is_trending": True,
        "genres": ["Action", "Adventure", "Drama"],
        "languages": ["English", "Hindi"],
        "cast": [("Ridley Scott", "Director"), ("Paul Mescal", "Lead Actor"), ("Pedro Pascal", "Supporting Actor")],
        "poster_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Joker",
        "description": "During the 1980s, a failed stand-up comedian is driven insane and turns to a life of crime and chaos in Gotham City.",
        "duration": 122,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=zAGVQLHvwOY",
        "release": "2019-10-04",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Crime", "Drama", "Thriller"],
        "languages": ["English", "Hindi"],
        "cast": [("Todd Phillips", "Director"), ("Joaquin Phoenix", "Lead Actor"), ("Robert De Niro", "Supporting Actor")],
        "poster_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Top Gun: Maverick",
        "description": "After thirty years, Maverick is still pushing the envelope as a top naval aviator, but must confront ghosts of his past when he trains a detachment.",
        "duration": 130,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=giXco2jaZ_4",
        "release": "2022-05-27",
        "rating": 4.9,
        "is_trending": True,
        "genres": ["Action", "Drama"],
        "languages": ["English", "Hindi"],
        "cast": [("Joseph Kosinski", "Director"), ("Tom Cruise", "Lead Actor"), ("Miles Teller", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "The Lord of the Rings: The Return of the King",
        "description": "Gandalf and Aragorn lead the World of Men against Sauron's army to draw his gaze from Frodo and Sam as they approach Mount Doom.",
        "duration": 201,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=r5X-hFf6Bwo",
        "release": "2003-12-17",
        "rating": 4.9,
        "is_trending": False,
        "genres": ["Action", "Adventure", "Fantasy"],
        "languages": ["English", "Hindi"],
        "cast": [("Peter Jackson", "Director"), ("Elijah Wood", "Lead Actor"), ("Viggo Mortensen", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Jurassic Park",
        "description": "A pragmatic paleontologist touring an almost complete theme park on an island in Central America is tasked with protecting two kids after a power failure.",
        "duration": 127,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=lc0UehYemQA",
        "release": "1993-06-11",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "languages": ["English", "Hindi"],
        "cast": [("Steven Spielberg", "Director"), ("Sam Neill", "Lead Actor"), ("Laura Dern", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Barbie",
        "description": "Barbie and Ken are having the time of their lives in the colorful and seemingly perfect world of Barbie Land. However, when they get a chance to go to the real world.",
        "duration": 114,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=pBk4NYhWNMM",
        "release": "2023-07-21",
        "rating": 4.5,
        "is_trending": True,
        "genres": ["Adventure", "Comedy", "Fantasy"],
        "languages": ["English", "Hindi"],
        "cast": [("Greta Gerwig", "Director"), ("Margot Robbie", "Lead Actress"), ("Ryan Gosling", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Deadpool & Wolverine",
        "description": "Wolverine is recovering from his injuries when he crosses paths with the loudmouth Deadpool. They team up to defeat a common enemy.",
        "duration": 128,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=73_1biulkYk",
        "release": "2024-07-26",
        "rating": 4.8,
        "is_trending": True,
        "genres": ["Action", "Adventure", "Comedy"],
        "languages": ["English", "Hindi", "Tamil", "Telugu"],
        "cast": [("Shawn Levy", "Director"), ("Ryan Reynolds", "Lead Actor"), ("Hugh Jackman", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Inside Out 2",
        "description": "Teenager Riley's mind headquarters is undergoing a sudden demolition to make room for something entirely unexpected: new Emotions!",
        "duration": 96,
        "age": "U",
        "trailer": "https://www.youtube.com/watch?v=LEjhY15eCx0",
        "release": "2024-06-14",
        "rating": 4.8,
        "is_trending": True,
        "genres": ["Animation", "Adventure", "Comedy"],
        "languages": ["English", "Hindi"],
        "cast": [("Kelsey Mann", "Director"), ("Amy Poehler", "Lead Voice"), ("Maya Hawke", "Lead Voice")],
        "poster_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "The Lion King",
        "description": "Lion prince Simba and his father are targeted by his bitter uncle, who wants to ascend the throne himself.",
        "duration": 88,
        "age": "U",
        "trailer": "https://www.youtube.com/watch?v=lFzVJEksoDY",
        "release": "1994-06-24",
        "rating": 4.9,
        "is_trending": False,
        "genres": ["Animation", "Adventure", "Drama"],
        "languages": ["English", "Hindi"],
        "cast": [("Roger Allers", "Director"), ("Matthew Broderick", "Lead Voice"), ("Jeremy Irons", "Lead Voice")],
        "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Spirited Away",
        "description": "During her family's move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods, witches, and spirits.",
        "duration": 125,
        "age": "U",
        "trailer": "https://www.youtube.com/watch?v=ByXuk9QqQkk",
        "release": "2001-07-20",
        "rating": 4.9,
        "is_trending": False,
        "genres": ["Animation", "Adventure", "Family"],
        "languages": ["Japanese", "English"],
        "cast": [("Hayao Miyazaki", "Director"), ("Rumi Hiiragi", "Lead Voice"), ("Miyu Irino", "Lead Voice")],
        "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Parasite",
        "description": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
        "duration": 132,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=5xH0HfJHsaY",
        "release": "2019-10-11",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Drama", "Thriller"],
        "languages": ["Korean", "English"],
        "cast": [("Bong Joon Ho", "Director"), ("Song Kang-ho", "Lead Actor"), ("Lee Sun-kyun", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Vikram",
        "description": "A high-octane action film where a special investigator is assigned a case of serial killings, which leads to a war between drug lords.",
        "duration": 175,
        "age": "A",
        "trailer": "https://www.youtube.com/watch?v=OKBMCL-frPU",
        "release": "2022-06-03",
        "rating": 4.8,
        "is_trending": False,
        "genres": ["Action", "Crime", "Thriller"],
        "languages": ["Tamil", "Hindi", "Telugu"],
        "cast": [("Lokesh Kanagaraj", "Director"), ("Kamal Haasan", "Lead Actor"), ("Vijay Sethupathi", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Pushpa 2: The Rule",
        "description": "Pushpa Raj expands his red sandalwood empire while facing intense opposition from police officer Bhanwar Singh Shekhawat.",
        "duration": 178,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=1kMK9H0S7pI",
        "release": "2024-12-05",
        "rating": 4.9,
        "is_trending": True,
        "genres": ["Action", "Crime", "Drama"],
        "languages": ["Telugu", "Hindi", "Tamil"],
        "cast": [("Sukumar", "Director"), ("Allu Arjun", "Lead Actor"), ("Rashmika Mandanna", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Kalki 2898 AD",
        "description": "A modern avatar of Vishnu, a Hindu god, who is believed to have descended to earth to protect the world from evil forces in a futuristic era.",
        "duration": 180,
        "age": "UA",
        "trailer": "https://www.youtube.com/watch?v=kQDd1AhGIHk",
        "release": "2024-06-27",
        "rating": 4.8,
        "is_trending": True,
        "genres": ["Action", "Sci-Fi", "Fantasy"],
        "languages": ["Telugu", "Hindi", "Tamil"],
        "cast": [("Nag Ashwin", "Director"), ("Prabhas", "Lead Actor"), ("Amitabh Bachchan", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Bajrangi Bhaijaan",
        "description": "An Indian man with a magnanimous heart takes a young mute Pakistani girl back to her homeland to reunite her with her family.",
        "duration": 159,
        "age": "U",
        "trailer": "https://www.youtube.com/watch?v=vyX4toD395U",
        "release": "2015-07-17",
        "rating": 4.9,
        "is_trending": False,
        "genres": ["Action", "Adventure", "Comedy"],
        "languages": ["Hindi"],
        "cast": [("Kabir Khan", "Director"), ("Salman Khan", "Lead Actor"), ("Kareena Kapoor", "Lead Actress")],
        "poster_url": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=500&auto=format&fit=crop&q=80"
    },
    {
        "name": "Zindagi Na Milegi Dobara",
        "description": "Three friends decide to turn their fantasy vacation into reality after one of them gets engaged, facing their fears along the way.",
        "duration": 155,
        "age": "U",
        "trailer": "https://www.youtube.com/watch?v=FJrpcbJ8tLg",
        "release": "2011-07-15",
        "rating": 4.9,
        "is_trending": False,
        "genres": ["Comedy", "Drama", "Romance"],
        "languages": ["Hindi"],
        "cast": [("Zoya Akhtar", "Director"), ("Hrithik Roshan", "Lead Actor"), ("Farhan Akhtar", "Lead Actor")],
        "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&auto=format&fit=crop&q=80"
    }
]

count = 0
for data in MOVIES_DATA:
    # 1. Genres safely checked by name or slug
    genre_objs = []
    for gname in data["genres"]:
        g_obj = Genre.objects.filter(name=gname).first()
        if not g_obj:
            gslug = slugify(gname)
            g_obj = Genre.objects.filter(slug=gslug).first()
            if not g_obj:
                g_obj = Genre.objects.create(name=gname, slug=gslug)
        genre_objs.append(g_obj)

    # 2. Languages safely checked
    lang_objs = []
    for lname in data["languages"]:
        code_map = {"English": "en", "Hindi": "hi", "Telugu": "te", "Tamil": "ta", "Kannada": "kn", "Japanese": "ja", "Korean": "ko"}
        l_obj = Language.objects.filter(name=lname).first()
        if not l_obj:
            l_obj = Language.objects.create(name=lname, code=code_map.get(lname, lname[:2].lower()))
        lang_objs.append(l_obj)

    # 3. Cast Members safely checked
    cast_objs = []
    for cname, crole in data["cast"]:
        c_obj = CastMember.objects.filter(name=cname, role=crole).first()
        if not c_obj:
            c_obj = CastMember.objects.create(name=cname, role=crole)
        cast_objs.append(c_obj)

    # 4. Save/Download Poster image safely
    filename = f"{slugify(data['name'])}_poster.jpg"
    image_rel_path = f"movies/{filename}"
    full_image_path = os.path.join(MEDIA_DIR, filename)

    if not os.path.exists(full_image_path):
        try:
            req = urllib.request.Request(data["poster_url"], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as resp, open(full_image_path, 'wb') as f:
                f.write(resp.read())
        except Exception:
            with open(full_image_path, 'wb') as f:
                f.write(b"")

    # 5. Movie object safely using get_or_create (preserves database integrity)
    release_dt = datetime.strptime(data["release"], "%Y-%m-%d").date()
    movie_obj = Movie.objects.filter(name=data["name"]).first()
    if not movie_obj:
        movie_obj = Movie.objects.create(
            name=data["name"],
            description=data["description"],
            duration_minutes=data["duration"],
            age_certification=data["age"],
            trailer_youtube_url=data["trailer"],
            release_date=release_dt,
            is_trending=data["is_trending"],
            rating=data["rating"],
            image=image_rel_path,
            cast=", ".join([c[0] for c in data["cast"]])
        )
    else:
        movie_obj.description = data["description"]
        movie_obj.duration_minutes = data["duration"]
        movie_obj.age_certification = data["age"]
        movie_obj.trailer_youtube_url = data["trailer"]
        movie_obj.release_date = release_dt
        movie_obj.is_trending = data["is_trending"]
        if not movie_obj.image:
            movie_obj.image = image_rel_path
        movie_obj.save()

    # Update relationships
    movie_obj.genres.set(genre_objs)
    movie_obj.languages.set(lang_objs)
    movie_obj.cast_members.set(cast_objs)

    # Create a theater showtime for each movie
    show_time = datetime.now() + timedelta(days=(count % 5) + 1, hours=(count * 2) % 12)
    theater_obj = Theater.objects.filter(name=f"PVR Cinema Hall {(count % 4) + 1}", movie=movie_obj).first()
    if not theater_obj:
        theater_obj = Theater.objects.create(
            name=f"PVR Cinema Hall {(count % 4) + 1}",
            movie=movie_obj,
            location=f"Screen {(count % 3) + 1}, Metro Mall",
            time=show_time,
            ticket_price=250.00 + ((count % 5) * 50)
        )

    # Create seats for theater if newly created
    for seat_num in ["A1", "A2", "A3", "B1", "B2", "C1", "C2"]:
        Seat.objects.get_or_create(theater=theater_obj, seat_number=seat_num)

    count += 1
    print(f"[{count}/52] Processed Movie: '{data['name']}' ({data['release'][:4]})")

print(f"\nSuccessfully populated {count} famous movies safely without affecting existing user data or database integrity!")
