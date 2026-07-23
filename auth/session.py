import jwt
import os
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET","nafasai-secret-key-change-in-production")

def create_token(uid: str, email: str) -> str:
    payload = {
        "uid":uid,
        "email":email,
        "exp":datetime.now(datetime.UTC) + timedelta(days=7)
    }

    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> dict:
    try:    
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"success": True, "uid": payload["uid"], "email": payload["email"]}
    except jwt.ExpiredSignatureError:
        return {"success": False, "error": "Session expired"}
    except jwt.InvalidTokenError:
        return {"success": False, "error": "Invalid token"}