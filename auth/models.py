# models.py
from sqlalchemy import Column, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .utils import hash_password

DATABASE_URL = "sqlite:///auth/users.db"

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True)
    password = Column(String)
    role = Column(String)

Base.metadata.create_all(engine)

def register_user(username, password, role="user"):
    session = Session()
    if session.query(User).filter_by(username=username).first():
        return {"success": False, "message": "User already exists."}
    user = User(username=username, password=hash_password(password), role=role)
    session.add(user)
    session.commit()
    return {"success": True, "message": "User registered successfully."}

def get_user_by_username(username):
    session = Session()
    return session.query(User).filter_by(username=username).first()
