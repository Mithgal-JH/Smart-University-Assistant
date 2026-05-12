import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, Header
from typing import Optional

# ✅ شغّل Firebase Admin مرة وحدة فقط
# حط مسار ملف serviceAccountKey.json هنا
_cred_path = os.getenv("FIREBASE_CREDENTIALS", "firebase_credentials.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(_cred_path)
    firebase_admin.initialize_app(cred)


def verify_firebase_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Dependency لـ FastAPI — يسحب التوكن من الـ Header ويتحقق منه.
    يرجع uid الخاص بالمستخدم عند النجاح.

    الاستخدام في الـ route:
        uid: str = Depends(verify_firebase_token)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="توكن المصادقة مفقود أو غير صحيح.")

    id_token = authorization.split("Bearer ")[1]

    try:
        decoded = auth.verify_id_token(id_token)
        return decoded["uid"]   # هاد هو user_id الحقيقي من Firebase

    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="انتهت صلاحية الجلسة، سجّل دخولك مجدداً.")

    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="توكن غير صالح.")

    except Exception as e:
        print(f"❌ Firebase auth error: {e}")
        raise HTTPException(status_code=401, detail="فشل التحقق من الهوية.")
