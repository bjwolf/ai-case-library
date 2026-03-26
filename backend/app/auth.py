import uuid
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

SECRET_KEY = "hackathon-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# --- Schemas ---
class UserRegister(BaseModel):
    login: str
    email: str
    display_name: str
    password: str

class UserLogin(BaseModel):
    login: str
    password: str

class UserResponse(BaseModel):
    id: str
    login: str
    email: str
    display_name: str
    role: str
    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


# --- Helpers ---
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = payload.get("sub")
        if login is None:
            return None
    except JWTError:
        return None
    return db.query(User).filter(User.login == login).first()

def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user

def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user

def send_reset_email(email: str, token: str, base_url: str = "http://127.0.0.1:8000"):
    """Send password reset email. For hackathon, prints to console instead of real SMTP."""
    reset_link = f"{base_url}/#reset-password?token={token}"
    print(f"\n{'='*60}")
    print(f"PASSWORD RESET EMAIL")
    print(f"To: {email}")
    print(f"Reset link: {reset_link}")
    print(f"Token: {token}")
    print(f"(Expires in 1 hour)")
    print(f"{'='*60}\n")
    # In production, replace with real SMTP:
    # msg = MIMEText(f"Click to reset: {reset_link}")
    # msg["Subject"] = "Password Reset - AI Case Library"
    # msg["To"] = email
    # with smtplib.SMTP("smtp.server.com", 587) as s:
    #     s.starttls(); s.login("user", "pass"); s.send_message(msg)
