from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

from ai_tutor_platform.db.pg_client import get_db_connection
from passlib.context import CryptContext

router = APIRouter()

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 setup for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# --- Token Management (replace with actual JWT library if deploying seriously) ---
# For simplicity, we'll use a basic token system. In production, use JWT.
SECRET_KEY = "your-super-secret-key" # CHANGE THIS IN PRODUCTION! Use an environment variable.
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserInDB(BaseModel):
    username: str
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT username, hashed_password FROM users WHERE username = %s", (username,))
        user_data = cur.fetchone()
        if user_data:
            return UserInDB(username=user_data[0], hashed_password=user_data[1])
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    # This is a very basic token. For production, use `jose` for JWT:
    # encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # For now, let's just make a simple string, but BE AWARE THIS IS NOT SECURE FOR REAL USE
    return f"{to_encode['username']}|{expire.isoformat()}" # Simple token for now

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # For production, you'd decode JWT here
    try:
        username, expiry_str = token.split('|')
        expire = datetime.fromisoformat(expiry_str)
        if datetime.utcnow() >= expire:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception
    return User(username=user.username, email=None) # Return basic user info

# --- Routes ---
@router.post("/signup", response_model=User)
def register_user(user: UserCreate):
    db_user = get_user(user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        hashed_password = get_password_hash(user.password)
        cur.execute(
            "INSERT INTO users (username, hashed_password, email) VALUES (%s, %s, %s)",
            (user.username, hashed_password, user.email)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to register user: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()
    
    return User(username=user.username, email=user.email)

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"username": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Dependency for protecting routes ---
# You can now add `user: User = Depends(get_current_user)` to any endpoint
# to require authentication.
