# models.py in FastAPI
from sqlalchemy import Column, Integer, String
from database import Base


# for production and dev database: AWS, supabase
class ShortStory(Base):
    __tablename__ = "amlit_shortstory"

    id = Column(Integer, primary_key=True)
    audio_url_en = Column(String, nullable=True)


class Chapter(Base):
    __tablename__ = "amlit_chapter"

    id = Column(Integer, primary_key=True)
    audio_url_en = Column(String, nullable=True)


class ChildrenStory(Base):
    __tablename__ = "amlit_childrenstory"

    id = Column(Integer, primary_key=True)
    audio_url_en = Column(String, nullable=True)
