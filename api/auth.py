"""Authentication and authorization for escrow agents."""
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.settings import settings
from models.database import get_db
from api.structured_logging import get_logger

logger = get_logger(__name__)

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# JWT configuration
SECRET_KEY = settings.encryption_key or "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class AgentRole(str, Enum):
    """Agent roles for RBAC."""
    ESCROW_AGENT = "escrow_agent"
    BUYER_AGENT = "buyer_agent"
    SELLER_AGENT = "seller_agent"
    TITLE_SEARCH_AGENT = "title_search_agent"
    INSPECTION_AGENT = "inspection_agent"
    APPRAISAL_AGENT = "appraisal_agent"
    LENDING_AGENT = "lending_agent"
    ADMIN = "admin"


class Permission(str, Enum):
    """Permissions for fine-grained access control."""
    # Transaction permissions
    CREATE_TRANSACTION = "create_transaction"
    READ_TRANSACTION = "read_transaction"
    UPDATE_TRANSACTION = "update_transaction"
    CANCEL_TRANSACTION = "cancel_transaction"
    
    # Verification permissions
    SUBMIT_VERIFICATION = "submit_verification"
    READ_VERIFICATION = "read_verification"
    APPROVE_VERIFICATION = "approve_verification"
    
    # Payment permissions
    RELEASE_PAYMENT = "release_payment"
    READ_PAYMENT = "read_payment"
    RETRY_PAYMENT = "retry_payment"
    
    # Settlement permissions
    EXECUTE_SETTLEMENT = "execute_settlement"
    READ_SETTLEMENT = "read_settlement"
    
    # Audit permissions
    READ_AUDIT_TRAIL = "read_audit_trail"
    VERIFY_BLOCKCHAIN_EVENT = "verify_blockchain_event"
    
    # Dispute permissions
    RAISE_DISPUTE = "raise_dispute"
    RESOLVE_DISPUTE = "resolve_dispute"
    
    # Admin permissions
    MANAGE_AGENTS = "manage_agents"
    RESET_CIRCUIT_BREAKERS = "reset_circuit_breakers"


# Role-Permission mapping
ROLE_PERMISSIONS = {
    AgentRole.ESCROW_AGENT: [
        Permission.CREATE_TRANSACTION,
        Permission.READ_TRANSACTION,
        Permission.UPDATE_TRANSACTION,
        Permission.CANCEL_TRANSACTION,
        Permission.READ_VERIFICATION,
        Permission.APPROVE_VERIFICATION,
        Permission.RELEASE_PAYMENT,
        Permission.READ_PAYMENT,
        Permission.RETRY_PAYMENT,
        Permission.EXECUTE_SETTLEMENT,
        Permission.READ_SETTLEMENT,
        Permission.READ_AUDIT_TRAIL,
        Permission.VERIFY_BLOCKCHAIN_EVENT,
        Permission.RESOLVE_DISPUTE,
    ],
    AgentRole.BUYER_AGENT: [
        Permission.CREATE_TRANSACTION,
        Permission.READ_TRANSACTION,
        Permission.READ_VERIFICATION,
        Permission.READ_PAYMENT,
        Permission.READ_SETTLEMENT,
        Permission.READ_AUDIT_TRAIL,
        Permission.RAISE_DISPUTE,
    ],
    AgentRole.SELLER_AGENT: [
        Permission.READ_TRANSACTION,
        Permission.READ_VERIFICATION,
        Permission.READ_PAYMENT,
        Permission.READ_SETTLEMENT,
        Permission.READ_AUDIT_TRAIL,
        Permission.RAISE_DISPUTE,
    ],
    AgentRole.TITLE_SEARCH_AGENT: [
        Permission.READ_TRANSACTION,
        Permission.SUBMIT_VERIFICATION,
        Permission.READ_VERIFICATION,
        Permission.READ_PAYMENT,
    ],
    AgentRole.INSPECTION_AGENT: [
        Permission.READ_TRANSACTION,
        Permission.SUBMIT_VERIFICATION,
        Permission.READ_VERIFICATION,
        Permission.READ_PAYMENT,
    ],
    AgentRole.APPRAISAL_AGENT: [
        Permission.READ_TRANSACTION,
        Permission.SUBMIT_VERIFICATION,
        Permission.READ_VERIFICATION,
        Permission.READ_PAYMENT,
    ],
    AgentRole.LENDING_AGENT: [
        Permission.READ_TRANSACTION,
        Permission.SUBMIT_VERIFICATION,
        Permission.READ_VERIFICATION,
    ],
    AgentRole.ADMIN: list(Permission),  # All permissions
}


class TokenData(BaseModel):
    """JWT token payload data."""
    agent_id: str
    role: AgentRole
    permissions: List[Permission]


class AgentCredentials(BaseModel):
    """Agent authentication credentials."""
    agent_id: str
    api_key: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    agent_id: str,
    role: AgentRole,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    permissions = ROLE_PERMISSIONS.get(role, [])
    
    to_encode = {
        "agent_id": agent_id,
        "role": role.value,
        "permissions": [p.value for p in permissions]
    }
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    logger.info(
        "access_token_created",
        agent_id=agent_id,
        role=role.value,
        expires_at=expire.isoformat()
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        agent_id: str = payload.get("agent_id")
        role: str = payload.get("role")
        permissions: List[str] = payload.get("permissions", [])
        
        if agent_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(
            agent_id=agent_id,
            role=AgentRole(role),
            permissions=[Permission(p) for p in permissions]
        )
    except JWTError as e:
        logger.error("jwt_decode_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> TokenData:
    """Dependency to get the current authenticated agent."""
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    logger.info(
        "agent_authenticated",
        agent_id=token_data.agent_id,
        role=token_data.role.value
    )
    
    return token_data


def require_role(allowed_roles: List[AgentRole]):
    """Dependency factory to require specific roles."""
    async def role_checker(
        current_agent: TokenData = Depends(get_current_agent)
    ) -> TokenData:
        if current_agent.role not in allowed_roles:
            logger.warning(
                "access_denied_role",
                agent_id=current_agent.agent_id,
                agent_role=current_agent.role.value,
                required_roles=[r.value for r in allowed_roles]
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_agent
    
    return role_checker


def require_permission(required_permission: Permission):
    """Dependency factory to require specific permission."""
    async def permission_checker(
        current_agent: TokenData = Depends(get_current_agent)
    ) -> TokenData:
        if required_permission not in current_agent.permissions:
            logger.warning(
                "access_denied_permission",
                agent_id=current_agent.agent_id,
                agent_role=current_agent.role.value,
                required_permission=required_permission.value
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {required_permission.value}"
            )
        return current_agent
    
    return permission_checker


def check_transaction_access(
    transaction_id: str,
    current_agent: TokenData,
    db: Session
) -> bool:
    """Check if agent has access to a specific transaction."""
    from models.transaction import Transaction
    
    # Escrow agents and admins have access to all transactions
    if current_agent.role in [AgentRole.ESCROW_AGENT, AgentRole.ADMIN]:
        return True
    
    # Get transaction
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        return False
    
    # Buyer and seller agents can only access their own transactions
    if current_agent.role == AgentRole.BUYER_AGENT:
        return transaction.buyer_agent_id == current_agent.agent_id
    
    if current_agent.role == AgentRole.SELLER_AGENT:
        return transaction.seller_agent_id == current_agent.agent_id
    
    # Verification agents can access transactions they're assigned to
    if current_agent.role in [
        AgentRole.TITLE_SEARCH_AGENT,
        AgentRole.INSPECTION_AGENT,
        AgentRole.APPRAISAL_AGENT,
        AgentRole.LENDING_AGENT
    ]:
        from models.verification import VerificationTask
        task = db.query(VerificationTask).filter(
            VerificationTask.transaction_id == transaction_id,
            VerificationTask.assigned_agent_id == current_agent.agent_id
        ).first()
        return task is not None
    
    return False


def check_wallet_access(current_agent: TokenData) -> bool:
    """Check if agent can trigger wallet operations (payments)."""
    # Only escrow agents can trigger payments
    if current_agent.role != AgentRole.ESCROW_AGENT:
        logger.warning(
            "wallet_access_denied",
            agent_id=current_agent.agent_id,
            agent_role=current_agent.role.value
        )
        return False
    
    return True


def require_wallet_access():
    """Dependency to require wallet access."""
    async def wallet_access_checker(
        current_agent: TokenData = Depends(get_current_agent)
    ) -> TokenData:
        if not check_wallet_access(current_agent):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Escrow Agents can trigger wallet operations"
            )
        return current_agent
    
    return wallet_access_checker
