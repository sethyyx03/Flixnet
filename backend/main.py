from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload  
from pydantic import BaseModel
from typing import List
from datetime import timedelta

from backend import database, models
from backend.auth import hash_password, verify_password, create_access_token, get_current_user

app = FastAPI()

# -----------------------
# Database Dependency
# -----------------------
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------
# Pydantic Schemas
# -----------------------

# --- Movies ---
class MovieBase(BaseModel):
    title: str
    description: str | None = None
    genre: str | None = None
    release_year: int | None = None
    rating: float | None = None
    thumbnail_url: str | None = None
    video_url: str | None = None

class MovieCreate(MovieBase):
    pass

class MovieOut(MovieBase):
    id: int

    class Config:
        orm_mode = True

# --- Watchlist ---
class WatchlistMovieOut(BaseModel):
    id: int
    title: str
    genre: str | None = None
    release_year: int | None = None
    rating: float | None = None
    thumbnail_url: str | None = None

    class Config:
        orm_mode = True

class WatchlistOut(BaseModel):
    id: int
    movie: WatchlistMovieOut   # 👈 nested movie details

    class Config:
        orm_mode = True

# --- Users ---
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# -----------------------
# Routes
# -----------------------
@app.get("/")
def root():
    return {"message": "Flixnet backend is running 🚀"}


# --- Movies ---
@app.get("/movies", response_model=List[MovieOut])
def get_movies(db: Session = Depends(get_db)):
    return db.query(models.Movie).all()

@app.get("/movies/{movie_id}", response_model=MovieOut)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

@app.post("/movies", response_model=MovieOut)
def create_movie(
    movie: MovieCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)  # 👈 require login
):
    db_movie = models.Movie(**movie.dict())
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

# --- Watchlist ---
@app.post("/watchlist/{movie_id}", response_model=WatchlistOut)
def add_to_watchlist(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    existing = db.query(models.Watchlist).filter_by(
        user_id=current_user, movie_id=movie_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already in watchlist")

    new_entry = models.Watchlist(user_id=current_user, movie_id=movie_id)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    # reload with movie details
    return db.query(models.Watchlist).options(joinedload(models.Watchlist.movie)).get(new_entry.id)


@app.get("/watchlist", response_model=List[WatchlistOut])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    return db.query(models.Watchlist).filter(models.Watchlist.user_id == current_user).all()


@app.delete("/watchlist/{movie_id}", response_model=WatchlistOut)
def remove_from_watchlist(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    entry = (
        db.query(models.Watchlist)
        .options(joinedload(models.Watchlist.movie))
        .filter_by(user_id=current_user, movie_id=movie_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Not in watchlist")

    db.delete(entry)
    db.commit()
    return entry


@app.get("/watchlist/{movie_id}", response_model=WatchlistOut)
def get_watchlist_item(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    entry = (
        db.query(models.Watchlist)
        .options(joinedload(models.Watchlist.movie))
        .filter_by(user_id=current_user, movie_id=movie_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Not in watchlist")
    return entry


@app.post("/watchlist/toggle/{movie_id}", response_model=WatchlistOut)
def toggle_watchlist(
    movie_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    # Check movie exists
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Check if already in watchlist
    entry = (
        db.query(models.Watchlist)
        .options(joinedload(models.Watchlist.movie))
        .filter_by(user_id=current_user, movie_id=movie_id)
        .first()
    )

    if entry:
        # If exists → remove it
        db.delete(entry)
        db.commit()
        entry.movie = movie  # keep movie info for response
        return entry  # still return movie details, but means "removed"
    else:
        # If not exists → add it
        new_entry = models.Watchlist(user_id=current_user, movie_id=movie_id)
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        return (
            db.query(models.Watchlist)
            .options(joinedload(models.Watchlist.movie))
            .get(new_entry.id)
        )


# --- Users (Auth) ---
@app.post("/signup", response_model=UserOut)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # check if email already exists
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    new_user = models.User(username=user.username, email=user.email, password_hash=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token({"sub": str(db_user.id)}, expires_delta=timedelta(minutes=60))
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me", response_model=UserOut)
def read_current_user(
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    user = db.query(models.User).filter(models.User.id == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
