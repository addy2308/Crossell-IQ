from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import sqlite3

router = APIRouter(prefix="/auth", tags=["Authentication"])
SECRET_KEY = "dev-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
# Use sha256_crypt instead of bcrypt – avoids version compatibility issues
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "agent"

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def init_db():
    conn = sqlite3.connect("users.db")
    conn.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, name TEXT, hashed_password TEXT, role TEXT)")
    # Add a default admin user (password: admin123)
    try:
        conn.execute("INSERT INTO users VALUES (?,?,?,?)",
                     ("admin@crosselliq.com", "Admin Kumar", pwd_context.hash("admin123"), "admin"))
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()

init_db()

@router.post("/login")
async def login(request: LoginRequest):
    conn = sqlite3.connect("users.db")
    user = conn.execute("SELECT * FROM users WHERE email=?", (request.email,)).fetchone()
    conn.close()
    if not user or not pwd_context.verify(request.password, user[2]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user[0], "name": user[1], "role": user[3]})
    return {"access_token": token, "token_type": "bearer", "name": user[1], "role": user[3], "agent_id": user[0]}

@router.post("/register")
async def register(request: RegisterRequest):
    conn = sqlite3.connect("users.db")
    try:
        conn.execute("INSERT INTO users VALUES (?,?,?,?)",
                     (request.email, request.name, pwd_context.hash(request.password), request.role))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    finally:
        conn.close()
    token = create_access_token({"sub": request.email, "name": request.name, "role": request.role})
    return {"access_token": token, "token_type": "bearer", "name": request.name, "role": request.role, "agent_id": request.email}
