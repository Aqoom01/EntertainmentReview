from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from models import User, Entertainment
from database import SessionLocal
import ServerInformation
import requests

import sys
import os

# 현재 스크립트 파일의 경로를 가져옵니다
current_dir = os.path.dirname(os.path.abspath(__file__))
# 상위 디렉토리를 추가합니다
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


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
    kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?response_type=code&client_id=${ServerInformation.REST_API_KEY}&redirect_uri=${ServerInformation.REDIRECT_URI}"
    return RedirectResponse(url=kakao_auth_url)

# 인증 코드 받기 및 액세스 토큰 요청
@app.post('/oAuth')
def oauth(request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get('code') 
    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": ServerInformation.REST_API_KEY,
        "redirect_uri": ServerInformation.REDIRECT_URI,
        "code": code,
    }
    token_response = requests.post(token_url, data=data)
    token_json = token_response.json()
    access_token = token_json.get("access_token")

    user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    user_info_response = requests.get(user_info_url, headers=headers)
    user_info = user_info_response.json()

    user = User(userId=user_info.get('id'))
    db.add(user)
    db.commit()
    
    return {"user_info": user_info, "message" : "주어진 ID를 사용하여 서비스를 이용할 수 있습니다."}

@app.post("/entertainment/{user_id}")
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

@app.get("/entertainment/{user_id}/specific")
def read_entertainment(user_id: str, data: SpecificEntertainmentReview, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.ID == user_id).first()
    checkValidateforUse(user, db)
    
    avg_score = db.query(func.avg(Entertainment.Score)).filter(Entertainment.workName == data.workName).scalar()
    
    if avg_score is None:
        raise HTTPException(status_code=404, detail="Entertainment not found")
    
    return {"score": avg_score}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)