from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from models import User, Entertainment
from database import SessionLocal
import threading
from datetime import datetime
import time

from middlewares import add_middlewares
from ratelimit import init_limiter, rate_limit
from auth import get_kakao_auth_url, get_kakao_token, get_kakao_user_info

app = FastAPI()
add_middlewares(app)

def background_task():
    while(True):
        current = datetime.now()
        if current.hour == 0 and current.minute == 0:
            with SessionLocal() as db:
                db.query(User).update({User.userAccess: 10})
                db.commit()
        else:
            time.sleep(60)

@app.on_event("startup")
async def startup():
    await init_limiter()
    
    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def checkValidateforUse(user_id: str, db: Session):
    user = db.query(User).filter(User.ID == user_id).first()
    if user == None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.userAccess == 0:
        raise HTTPException(status_code=403, detail="Access is finished.")
    else:
        user.userAccess = user.userAccess - 1
        db.commit()

class CreateUserRequest(BaseModel):
    id: int

class SpecificEntertainmentReview(BaseModel):
    workName: str


@app.get('/login')
def login():
    return {"url": get_kakao_auth_url()}


@app.get('/kakaoAuth')
def oauth(request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get('code') 
    access_token = get_kakao_token(code)
    user_info = get_kakao_user_info(access_token)
    
    user = User(ID=user_info.get('id'))
    if db.query(User).filter(User.ID == user_info.get('id')).first() is None:
        db.add(user)
        db.commit()
    
    return {"user_id": user_info.get('id'), "message": "주어진 ID를 사용하여 서비스를 이용할 수 있습니다."}


@app.get("/entertainment/{user_id}")
@rate_limit(times=10, seconds=60)
def top10Review(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.ID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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


@app.get("/entertainment/{user_id}/specific")
@rate_limit(times=5, seconds=60)
def read_entertainment(user_id: str, workName: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.ID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    avg_score = db.query(func.avg(Entertainment.Score)).filter(Entertainment.workName == workName).scalar()
    
    if avg_score is None:
        raise HTTPException(status_code=404, detail="Entertainment not found")
    
    return {"score": avg_score}