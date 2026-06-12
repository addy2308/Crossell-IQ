from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Dict, Optional
from datetime import datetime

from app.models.customer import Customer, Agent


class AgentService:
    """Service for agent-related operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_agent_queue(
        self, 
        agent_id: str, 
        limit: int = 10
    ) -> List[Dict]:
        """Get prioritized customer queue for an agent."""
        # Get agent
        result = await self.db.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        agent = result.scalar_one_or_none()
        
        if not agent:
            return []
        
        assigned_ids = agent.assigned_customers or []
        if not assigned_ids:
            return []
        
        # Get customers sorted by propensity
        result = await self.db.execute(
            select(Customer)
            .where(
                and_(
                    Customer.customer_id.in_(assigned_ids),
                    Customer.latest_propensity_score > 0.2
                )
            )
            .order_by(Customer.latest_propensity_score.desc())
            .limit(limit)
        )
        customers = result.scalars().all()
        
        queue = []
        for cust in customers:
            urgency = self._calculate_urgency(cust)
            reasoning = self._generate_reasoning(cust)
            channel = self._suggest_channel(cust, urgency)
            
            queue.append({
                "customer_id": cust.customer_id,
                "propensity_score": round(cust.latest_propensity_score, 4),
                "recommended_product": cust.latest_recommended_product or "Standard Upgrade",
                "urgency": urgency,
                "reasoning": reasoning,
                "suggested_channel": channel
            })
        
        return queue
    
    def _calculate_urgency(self, customer: Customer) -> str:
        """Calculate urgency level based on customer attributes."""
        score = 0
        
        if customer.latest_propensity_score:
            score += customer.latest_propensity_score * 5
        
        if customer.renewal_in_30_days:
            score += 3
        if customer.had_claim_60d:
            score += 2
        if customer.days_since_service and customer.days_since_service < 30:
            score += 1
        
        if score >= 7:
            return "high"
        elif score >= 4:
            return "medium"
        else:
            return "low"
    
    def _generate_reasoning(self, customer: Customer) -> str:
        """Generate human-readable reasoning for the recommendation."""
        reasons = []
        
        if customer.renewal_in_30_days:
            reasons.append("Policy renewal in next 30 days")
        if customer.had_claim_60d:
            reasons.append("Recent claim filed")
        if customer.days_since_service and customer.days_since_service < 90:
            reasons.append("Recent service visit")
        if customer.lost_quotation_count and customer.lost_quotation_count > 0:
            reasons.append(f"{customer.lost_quotation_count} previous lost quotations")
        if customer.engagement_score and customer.engagement_score > 0.7:
            reasons.append("High digital engagement")
        if customer.monetary and customer.monetary > 15000:
            reasons.append("High-value customer")
        
        return ", ".join(reasons) if reasons else "Customer ready for upsell opportunity"
    
    def _suggest_channel(self, customer: Customer, urgency: str) -> str:
        """Suggest the best communication channel."""
        if urgency == "high":
            return "phone"
        elif customer.engagement_score and customer.engagement_score > 0.6:
            return "email"
        else:
            return "whatsapp"