import os
import firebase_admin
from firebase_admin import credentials, auth, firestore
from dotenv import load_dotenv

load_dotenv()

cred = credentials.Certificate(
    os.getenv("FIREBASE_CREDENTIALS_PATH","firebase_credentials.json")
)

firebase_admin.initialize_app(cred)

db = firestore.client()

def create_user(email: str, password: str, name: str, default_city: str, health_profile: str) -> dict:
    try:
        user = auth.create_user(email=email, password=password, display_name=name)
        db.collection("users").document(user.uid).set({
            "name":name,
            "email":email,
            "default_city":default_city,
            "health_profile":health_profile,
            "created_at":firestore.SERVER_TIMESTAMP
        })
        return {"success":True,"uid":user.uid}

    except Exception as e:
        return {"success": False, "error": str(e)}

def get_user_profile(uid: str) -> dict:
    doc = db.collection("users").document(uid).get()
    if doc.exists:
        return {"success": True, "profile": doc.to_dict()}
    return {"success": False, "error": "User not found"}

def update_user_defaults(uid: str, city: str, profile: str) -> dict:
    try:
        db.collection("users").document(uid).update({
            "default_city": city,
            "health_profile": profile
        })
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}