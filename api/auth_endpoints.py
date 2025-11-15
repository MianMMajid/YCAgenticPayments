"""Authentication endpoints for agent login and token management."""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.auth import (
    create_access_token,
    verify_password,
    get_password_hash,
    AgentRole,
    get_current_agent,
    TokenData,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from models.database import get_db
from models.agent import Agent
from api.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    """Login request payload."""
    agent_id: str
    api_key: str


class LoginResponse(BaseModel):
    """Login response with access token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
    agent_id: str
    role: str


class RegisterAgentRequest(BaseModel):
    """Register new agent request."""
    agent_id: str
    name: str
    email: str
    api_key: str
    role: AgentRole


class AgentResponse(BaseModel):
    """Agent information response."""
    id: str
    agent_id: str
    name: str
    email: str
    role: str
    is_active: bool


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate an agent and return a JWT access token.
    
    The agent must provide their agent_id and api_key.
    """
    # Find agent by agent_id
    agent = db.query(Agent).filter(
        Agent.agent_id == request.agent_id,
        Agent.is_active == True
    ).first()
    
    if not agent:
        logger.warning("login_failed_agent_not_found", agent_id=request.agent_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify API key
    if not verify_password(request.api_key, agent.api_key_hash):
        logger.warning("login_failed_invalid_api_key", agent_id=request.agent_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Update last login
    from datetime import datetime
    agent.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(
        agent_id=agent.agent_id,
        role=AgentRole(agent.role),
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    logger.info(
        "login_successful",
        agent_id=agent.agent_id,
        role=agent.role
    )
    
    return LoginResponse(
        access_token=access_token,
        agent_id=agent.agent_id,
        role=agent.role
    )


@router.post("/register", response_model=AgentResponse)
async def register_agent(
    request: RegisterAgentRequest,
    db: Session = Depends(get_db),
    current_agent: TokenData = Depends(get_current_agent)
):
    """
    Register a new agent (admin only).
    
    Only agents with ADMIN role can register new agents.
    """
    # Check if current agent is admin
    if current_agent.role != AgentRole.ADMIN:
        logger.warning(
            "register_agent_denied",
            agent_id=current_agent.agent_id,
            role=current_agent.role.value
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can register new agents"
        )
    
    # Check if agent_id already exists
    existing_agent = db.query(Agent).filter(
        Agent.agent_id == request.agent_id
    ).first()
    
    if existing_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent ID already exists"
        )
    
    # Hash API key
    api_key_hash = get_password_hash(request.api_key)
    
    # Create new agent
    new_agent = Agent(
        agent_id=request.agent_id,
        name=request.name,
        email=request.email,
        api_key_hash=api_key_hash,
        role=request.role.value,
        is_active=True
    )
    
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    
    logger.info(
        "agent_registered",
        agent_id=new_agent.agent_id,
        role=new_agent.role,
        registered_by=current_agent.agent_id
    )
    
    return AgentResponse(
        id=new_agent.id,
        agent_id=new_agent.agent_id,
        name=new_agent.name,
        email=new_agent.email,
        role=new_agent.role,
        is_active=new_agent.is_active
    )


@router.get("/me", response_model=AgentResponse)
async def get_current_agent_info(
    current_agent: TokenData = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Get current authenticated agent information."""
    agent = db.query(Agent).filter(
        Agent.agent_id == current_agent.agent_id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return AgentResponse(
        id=agent.id,
        agent_id=agent.agent_id,
        name=agent.name,
        email=agent.email,
        role=agent.role,
        is_active=agent.is_active
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    current_agent: TokenData = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """Refresh access token for current agent."""
    # Verify agent still exists and is active
    agent = db.query(Agent).filter(
        Agent.agent_id == current_agent.agent_id,
        Agent.is_active == True
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent not found or inactive"
        )
    
    # Create new access token
    access_token = create_access_token(
        agent_id=agent.agent_id,
        role=AgentRole(agent.role),
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    logger.info(
        "token_refreshed",
        agent_id=agent.agent_id,
        role=agent.role
    )
    
    return LoginResponse(
        access_token=access_token,
        agent_id=agent.agent_id,
        role=agent.role
    )
