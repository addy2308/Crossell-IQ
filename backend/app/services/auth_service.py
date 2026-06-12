from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from passlib.context import CryptContext
from app.models.customer import Agent, AuditLog
from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def authenticate(self, email: str, password: str) -> Optional[Agent]:
        result = await self.db.execute(select(Agent).where(Agent.email == email, Agent.is_active == True))
        agent = result.scalar_one_or_none()
        
        if not agent or not pwd_context.verify(password, agent.hashed_password):
            return None
        
        agent.last_login = datetime.utcnow()
        await self.db.commit()
        
        return agent
    
    def create_token(self, agent: Agent) -> str:
        payload = {
            "sub": agent.agent_id,
            "name": agent.name,
            "email": agent.email,
            "role": agent.role,
            "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except:
            return None
    
    async def create_agent(self, name: str, email: str, password: str, role: str = "agent", region: str = None) -> Agent:
        agent = Agent(
            agent_id=f"AGT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            name=name,
            email=email,
            hashed_password=pwd_context.hash(password),
            role=role,
            region=region
        )
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)
        
        await self.log_audit(agent.agent_id, "agent_created", f"Agent {name} created")
        return agent
    
    async def log_audit(self, user_id: str, action: str, details: str = None):
        log = AuditLog(user_id=user_id, action=action, details={"description": details} if details else None)
        self.db.add(log)
        await self.db.commit()
    
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
