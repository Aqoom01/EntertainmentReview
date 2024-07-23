from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

import sys
import os

# 현재 스크립트 파일의 경로를 가져옵니다
current_dir = os.path.dirname(os.path.abspath(__file__))
# 상위 디렉토리를 추가합니다
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from models import User, Entertainment
from database import SessionLocal, engine, Base

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def checkValidateforCreate(user: User, db: Session):
    if user != None:
        raise HTTPException(status_code=403, detail="This ID is working")
        


def checkValidateforUse(user: User, db: Session):
    if user.ID == None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.userAccess == 0:
        db.delete(user)
        db.commit()
        raise HTTPException(status_code=403, detail="Access is finished.")
    else:
        user.userAccess = user.userAccess - 1
        db.commit()

class CreateUserRequest(BaseModel):
    id: str
    name: str
    password: str
    phone: str

@app.post("/entertainment")
def create_user(data: CreateUserRequest, db: Session = Depends(get_db)):
    forcheck = db.query(User).filter(User.ID == data.id).first()
    checkValidateforCreate(forcheck, db)
    
    db_user = User(ID = data.id, userName=data.name, userPassword=data.password, userPhone=data.phone, userAccess = 10)
    db.add(db_user)
    db.commit()
    return {"your_ID" : db_user.ID , "detail" : "Now you can use with this ID"}


@app.get("/entertainment/{user_id}")
def top10Review(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.ID == user_id).first()
    checkValidateforUse(user, db)

    # Query for top 10 reviews
    top10 = db.query(
        Entertainment.workName,
        func.avg(Entertainment.Score).label('avg_score'),
        func.count(Entertainment.ID).label('item_count')
    ).group_by(Entertainment.workName) \
    .order_by(func.avg(Entertainment.Score).desc(), func.count(Entertainment.ID).desc()) \
    .limit(10) \
    .all()

    # Transforming the query result into a list of dictionaries
    result = [{"workName": item[0], "avg_score": item[1], "item_count": item[2]} for item in top10]

    return result

@app.get("/entertainment/{user_id}}/{entertainment_name}")
def read_entertainment(user_id: str, entertainment_name: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.ID == user_id).first()
    checkValidateforUse(user, db)
    
    avg_score = db.query(func.avg(Entertainment.Score)).filter(Entertainment.workName == entertainment_name).scalar()
    
    if avg_score is None:
        raise HTTPException(status_code=404, detail="Entertainment not found")
    
    return {"score": avg_score}
