from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "agent"
    region: str = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    name: str
    role: str
    agent_id: str

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth = AuthService(db)
    agent = await auth.authenticate(request.email, request.password)
    
    if not agent:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    token = auth.create_token(agent)
    await auth.log_audit(agent.agent_id, "login", "User logged in")
    
    return TokenResponse(
        access_token=token,
        name=agent.name,
        role=agent.role,
        agent_id=agent.agent_id
    )

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    auth = AuthService(db)
    
    try:
        agent = await auth.create_agent(request.name, request.email, request.password, request.role, request.region)
        token = auth.create_token(agent)
        return TokenResponse(access_token=token, name=agent.name, role=agent.role, agent_id=agent.agent_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
