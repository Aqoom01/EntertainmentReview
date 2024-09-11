import requests
from fastapi import HTTPException, Request
import ServerInformation

def get_kakao_auth_url():
    return f"https://kauth.kakao.com/oauth/authorize?response_type=code&client_id={ServerInformation.REST_API_KEY}&redirect_uri={ServerInformation.REDIRECT_URI}"

def get_kakao_token(code: str):
    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": ServerInformation.REST_API_KEY,
        "redirect_uri": ServerInformation.REDIRECT_URI,
        "code": code,
    }
    token_response = requests.post(token_url, data=data)
    if token_response.status_code != 200:
        raise HTTPException(status_code=token_response.status_code, detail="Failed to get Kakao token")
    
    return token_response.json().get("access_token")

def get_kakao_user_info(access_token: str):
    user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_info_response = requests.get(user_info_url, headers=headers)
    if user_info_response.status_code != 200:
        raise HTTPException(status_code=user_info_response.status_code, detail="Failed to get user info")
    
    return user_info_response.json()
