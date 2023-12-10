from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.params import Depends
from sqlalchemy import create_engine, String, Column, Integer
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
import logging

# Create a custom logger
logger = logging.getLogger(__name__)

# Set level of logger
logger.setLevel(logging.DEBUG)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('file.log')
c_handler.setLevel(logging.INFO)
f_handler.setLevel(logging.INFO)

# Create formatters and add it to handlers
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

Base = declarative_base()

class Item(BaseModel):
    id: int
    name: str
    description: Optional[str]


class ItemCreate(BaseModel):
    name: str
    description: Optional[str]


class ItemUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]


DATABASE_URL = "sqlite:///test.db"





class DBItem(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String, nullable=True)


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger.info("SessionLocal created")

app = FastAPI()


# Dependency to get the database session
def get_db():
    logger.info("Getting database session... main")
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


@app.on_event("startup")
async def startup_event():
    logger.info("Creating database tables...main")
    Base.metadata.create_all(bind=engine)


@app.get("/items")
def read_items(db: Session = Depends(get_db)) -> list[Item]:
    db_items = db.query(DBItem).all()
    return [Item(**db_item.__dict__) for db_item in db_items]

@app.post("/items")
def create_item(item: ItemCreate, db: Session = Depends(get_db)) -> Item:
    db_item = DBItem(**item.__dict__)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return Item(**db_item.__dict__)


@app.get("/items/{item_id}")
def read_item(item_id: int, db: Session = Depends(get_db)) -> Item:
    db_item = db.query(DBItem).filter(DBItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(**db_item.__dict__)


@app.put("/items/{item_id}")
def update_item(item_id: int, item: ItemUpdate, db: Session = Depends(get_db)) -> Item:
    db_item = db.query(DBItem).filter(DBItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in item.__dict__.items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return Item(**db_item.__dict__)


@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)) -> Item:
    db_item = db.query(DBItem).filter(DBItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return Item(**db_item.__dict__)
