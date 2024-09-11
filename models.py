from sqlalchemy import Column, Integer, String, Date, BigInteger
from sqlalchemy.orm import validates, declarative_base

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from database import Base

class Entertainment(Base):
    __tablename__ = "entertainment"

    ID = Column(Integer, primary_key=True, index=True)
    workName = Column(String(50))
    Category = Column(String(20))
    Score = Column(Integer)
    Writer = Column(String(20))
    NTCE_DE = Column(Date)

class User(Base):
    __tablename__ = "user"
    
    ID = Column(BigInteger, primary_key=True, index=True)
    userAccess = Column(Integer, default=10)

@validates("userAccess")
def validate_access(self, access):
    if access < 0:
        raise ValueError("Access is finished.")
    return access