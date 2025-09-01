from sqlalchemy import Column, Integer, String, Float, ForeignKey, TIMESTAMP, Text
from sqlalchemy.sql import func
from .database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Movie(Base):
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    genre = Column(String(50))
    release_year = Column(Integer)
    rating = Column(Float)
    thumbnail_url = Column(Text)
    video_url = Column(Text)

class Watchlist(Base):
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"))
    added_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    movie = relationship("Movie")  # gives access to movie details