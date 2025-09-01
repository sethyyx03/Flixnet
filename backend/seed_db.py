from backend.database import SessionLocal
from backend.models import Movie

# Open a DB session
db = SessionLocal()

# Sample movies
movies = [
    Movie(
        title="Inception",
        description="A skilled thief leads a team into people's dreams.",
        genre="Sci-Fi",
        release_year=2010,
        rating=8.8,
        thumbnail_url="https://image.tmdb.org/t/p/w500/qmDpIHrmpJINaRKAfWQfftjCdyi.jpg",
        video_url="https://example.com/inception.mp4"
    ),
    Movie(
        title="Stranger Things",
        description="A group of kids uncover a secret lab and a strange girl with powers.",
        genre="Drama",
        release_year=2016,
        rating=8.7,
        thumbnail_url="https://image.tmdb.org/t/p/w500/x2LSRK2Cm7MZhjluni1msVJ3wDF.jpg",
        video_url="https://example.com/strangerthings.mp4"
    ),
    Movie(
        title="The Dark Knight",
        description="Batman faces his toughest challenge against the Joker.",
        genre="Action",
        release_year=2008,
        rating=9.0,
        thumbnail_url="https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        video_url="https://example.com/darkknight.mp4"
    ),
]

# Add movies if not already in DB
for movie in movies:
    existing = db.query(Movie).filter(Movie.title == movie.title).first()
    if not existing:
        db.add(movie)

db.commit()
db.close()

print("✅ Database seeded with movies!")
