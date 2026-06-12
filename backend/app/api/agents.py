from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.customer import Agent, Customer, Feedback
from app.api.auth import get_current_agent

router = APIRouter()


@router.get("/me")
async def get_current_agent_info(
    current_agent: Agent = Depends(get_current_agent)
):
    """Get current authenticated agent's information."""
    return {
        "agent_id": current_agent.agent_id,
        "name": current_agent.name,
        "email": current_agent.email,
        "region": current_agent.region,
        "role": current_agent.role,
        "assigned_customers_count": len(current_agent.assigned_customers or []),
        "last_login": current_agent.last_login
    }


@router.get("/performance")
async def get_agent_performance(
    agent_id: Optional[str] = Query(None),
    days: int = Query(default=30, le=90),
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Get agent performance metrics."""
    target_agent_id = agent_id or current_agent.agent_id
    
    # Only managers/admins can view other agents
    if target_agent_id != current_agent.agent_id and current_agent.role not in ["manager", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to view other agents")
    
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get feedback counts
    result = await db.execute(
        select(
            Feedback.action_taken,
            func.count(Feedback.id).label('count')
        )
        .where(
            Feedback.agent_id == target_agent_id,
            Feedback.created_at >= since_date
        )
        .group_by(Feedback.action_taken)
    )
    action_counts = {row.action_taken: row.count for row in result}
    
    # Get conversion count
    result = await db.execute(
        select(func.count(Feedback.id))
        .where(
            Feedback.agent_id == target_agent_id,
            Feedback.outcome == "converted",
            Feedback.created_at >= since_date
        )
    )
    conversions = result.scalar() or 0
    
    total_actions = sum(action_counts.values())
    activation_rate = (total_actions / max(len(current_agent.assigned_customers or []), 1)) * 100
    
    return {
        "agent_id": target_agent_id,
        "period_days": days,
        "total_actions": total_actions,
        "action_breakdown": action_counts,
        "conversions": conversions,
        "conversion_rate": (conversions / max(total_actions, 1)) * 100,
        "activation_rate": round(activation_rate, 2)
    }


@router.get("/leaderboard")
async def get_agent_leaderboard(
    days: int = Query(default=30, le=90),
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Get agent performance leaderboard."""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(
            Feedback.agent_id,
            Agent.name,
            func.count(Feedback.id).label('total_actions'),
            func.sum(
                func.case((Feedback.outcome == "converted", 1), else_=0)
            ).label('conversions')
        )
        .join(Agent, Feedback.agent_id == Agent.agent_id)
        .where(Feedback.created_at >= since_date)
        .group_by(Feedback.agent_id, Agent.name)
        .order_by(func.count(Feedback.id).desc())
        .limit(limit)
    )
    
    leaderboard = []
    for row in result:
        leaderboard.append({
            "agent_id": row.agent_id,
            "name": row.name,
            "total_actions": row.total_actions,
            "conversions": row.conversions,
            "conversion_rate": round((row.conversions / max(row.total_actions, 1)) * 100, 2)
        })
    
    return leaderboard