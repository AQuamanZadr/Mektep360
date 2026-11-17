from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Пароль от твоей базы данных
URL = "postgresql://postgres:mojitos1234@localhost:5432/postgres"

Base = declarative_base()
engine = create_engine(URL)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "school_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True) # Email
    password = Column(String) # Пароль
    first_name = Column(String)
    last_name = Column(String)
    grade = Column(String)
    coins = Column(Integer, default=10)
    is_admin = Column(Boolean, default=False)
    profile_image = Column(String, default="")
    
    meals = relationship("Meal", back_populates="owner")

class Meal(Base):
    __tablename__ = "meals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("school_users.id"))
    date = Column(String) 
    meal_type = Column(String)
    owner = relationship("User", back_populates="meals")

def init_db():
    Base.metadata.create_all(bind=engine)