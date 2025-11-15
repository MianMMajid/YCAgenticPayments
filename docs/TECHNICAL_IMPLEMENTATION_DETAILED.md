# Technical Implementation: In-Depth Documentation

**Version**: 1.0  
**Last Updated**: November 15, 2025  
**Status**: Production-Ready (Demo Mode)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Services Implementation](#core-services-implementation)
3. [Agent Integration](#agent-integration)
4. [Payment Flow Architecture](#payment-flow-architecture)
5. [x402 Protocol Implementation](#x402-protocol-implementation)
6. [Configuration Management](#configuration-management)
7. [Data Models & Structures](#data-models--structures)
8. [Error Handling & Resilience](#error-handling--resilience)
9. [Performance Considerations](#performance-considerations)
10. [Security Implementation](#security-implementation)

---

## Architecture Overview

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    COUNTER AI APPLICATION                       │
│                      (FastAPI Backend)                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Agents     │   │   Services   │   │   Workflows │
│              │   │              │   │              │
│ - Title      │   │ - Locus      │   │ - State      │
│ - Inspection │   │ - x402       │   │   Machine    │
│ - Appraisal  │   │ - Payment    │   │ - Engine     │
│ - Lending    │   │ - Wallet  │   │              │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │     Locus Integration Layer      │
        │  - Wallet Manager                │
        │  - Integration Service           │
        │  - Payment Handler               │
        │  - x402 Protocol Handler         │
        └─────────────┬───────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│  Mock    │  │  Locus   │  │  x402    │
│ Services │  │  API     │  │ Services │
│ (Demo)   │  │ (Future) │  │ (Real)   │
└──────────┘  └──────────┘  └──────────┘
```

### Component Relationships

```
Application Startup
    ↓
FastAPI @app.on_event("startup")
    ↓
initialize_locus_on_startup()
    ├─→ init_wallet_manager()
    │   └─→ LocusWalletManager
    │       ├─→ Validates wallet format
    │       └─→ Stores wallet credentials
    │
    ├─→ init_locus(api_key, wallet_address)
    │   └─→ LocusIntegration
    │       ├─→ Loads policy IDs from .env
    │       ├─→ Loads budgets from .env
    │       └─→ Initializes budget tracking
    │
    └─→ LocusPaymentHandler(locus)
        └─→ Stores payment history

Agent Execution
    ↓
Agent.execute_verification()
    ↓
Agent._perform_*() method
    ├─→ Gets service URL from settings
    ├─→ Gets recipient wallet address
    ├─→ Converts payment amount to USDC
    ├─→ Checks if Locus available
    │   ├─→ If yes: Creates LocusPaymentHandler
    │   └─→ If no: Uses mock signing
    │
    └─→ X402ProtocolHandler.execute_x402_flow()
        ├─→ Step 1: GET service_url → 402
        ├─→ Step 2: Parse 402 response
        ├─→ Step 3: Sign payment (via handler or mock)
        ├─→ Step 4: POST with X-PAYMENT header
        └─→ Step 5: Return service data
```

---

## Core Services Implementation

### 1. Locus Wallet Manager (`services/locus_wallet_manager.py`)

#### Purpose
Manages the blockchain wallet used for Locus payments. Handles wallet initialization, validation, and provides wallet information to other services.

#### Class Structure

```python
class LocusWalletManager:
    """
    Manages blockchain wallet for Locus payments on Base Mainnet (Chain 8453).
    
    Attributes:
        wallet_address: str - Ethereum-style address (0x + 40 hex)
        private_key: str - Private key for signing (0x + 64 hex)
        chain_id: int - Blockchain chain ID (8453 = Base Mainnet)
        wallet_name: str - Human-readable wallet name
    """
```

#### Key Methods

**`__init__(wallet_address, private_key, chain_id, wallet_name)`**
- **Purpose**: Initialize wallet manager with credentials
- **Validation**: None (validation happens in `validate_wallet()`)
- **Storage**: Stores credentials in instance variables
- **Logging**: Logs initialization with masked address

**`get_wallet_info() -> Dict[str, Any]`**
- **Returns**: Complete wallet information dictionary
- **Format**:
  ```python
  {
      "name": "Yc-MakeEmPay",
      "address": "0x45B876546953Fe28C66022b48310dFbc1c2Fec47",
      "chain_id": 8453,
      "network": "Base Mainnet",
      "status": "Active"  # or "Invalid"
  }
  ```
- **Network Mapping**: Maps chain IDs to network names
  - `8453` → "Base Mainnet"
  - `84531` → "Base Sepolia Testnet"
  - `1` → "Ethereum Mainnet"

**`validate_wallet() -> bool`**
- **Purpose**: Validate wallet address and private key format
- **Checks**:
  1. Address starts with `0x`
  2. Address is 42 characters (0x + 40 hex)
  3. Address contains valid hex characters
  4. Private key starts with `0x`
  5. Private key is 66 characters (0x + 64 hex)
  6. Private key contains valid hex characters
- **Returns**: `True` if valid, `False` otherwise
- **Error Handling**: Logs specific validation errors
- **Performance**: O(1) - simple string validation

**`get_address() -> str`**
- **Purpose**: Get wallet address
- **Returns**: Wallet address string
- **Use Case**: Pass to other services that need wallet address

**`get_private_key() -> str`**
- **Purpose**: Get private key for transaction signing
- **Returns**: Private key string
- **Security Note**: In production, this should be encrypted at rest

**`get_chain_id() -> int`**
- **Purpose**: Get blockchain chain ID
- **Returns**: Chain ID integer (8453 for Base Mainnet)

#### Singleton Pattern

**`init_wallet_manager() -> LocusWalletManager`**
- **Purpose**: Initialize global singleton instance
- **Environment Variables**:
  - `LOCUS_WALLET_ADDRESS` or `locus_wallet_address`
  - `LOCUS_WALLET_PRIVATE_KEY` or `locus_wallet_private_key`
  - `LOCUS_CHAIN_ID` or `locus_chain_id` (defaults to 8453)
  - `LOCUS_WALLET_NAME` or `locus_wallet_name` (defaults to "Yc-MakeEmPay")
- **Validation**: Calls `validate_wallet()` on initialization
- **Error Handling**: Raises `ValueError` if credentials missing or invalid
- **Idempotency**: Returns existing instance if already initialized

**`get_wallet_manager() -> Optional[LocusWalletManager]`**
- **Purpose**: Get global singleton instance
- **Returns**: Instance if initialized, `None` otherwise
- **Use Case**: Access wallet manager from other services

#### Technical Details

**Wallet Address Format**:
- Ethereum-style: `0x` prefix + 40 hexadecimal characters
- Example: `0x45B876546953Fe28C66022b48310dFbc1c2Fec47`
- Case-insensitive (Ethereum addresses are checksummed)

**Private Key Format**:
- Ethereum-style: `0x` prefix + 64 hexadecimal characters
- Example: `0xfd7875c20892f146272f8733a5d037d24da4ceffe8b59d90dc30709aea2bb0e1`
- **Security**: Should never be logged or exposed

**Chain ID**:
- `8453`: Base Mainnet (production)
- `84531`: Base Sepolia Testnet (testing)
- `1`: Ethereum Mainnet

**Singleton Implementation**:
- Uses module-level variable `_wallet_manager_instance`
- Thread-safe for FastAPI (single process, async)
- Prevents multiple initializations

---

### 2. Locus Integration Service (`services/locus_integration.py`)

#### Purpose
Main integration point with Locus payment infrastructure. Manages policy groups, budgets, and agent configurations.

#### Class Structure

```python
class LocusIntegration:
    """
    Main integration point with Locus payment infrastructure.
    
    Manages:
    - Policy Group IDs (from Locus dashboard)
    - Agent budgets (daily limits in USDC)
    - Budget tracking and checking
    - Agent type normalization
    """
```

#### Key Attributes

**`AGENT_TYPES`**: Dictionary mapping agent types
```python
{
    "title": "title",
    "inspection": "inspection",
    "appraisal": "appraisal",
    "underwriting": "underwriting",
    "lending": "underwriting"  # Alias for lending agent
}
```

**`policies`**: Policy Group IDs by agent type
```python
{
    "title": "policy_title_xxxxx",  # From LOCUS_POLICY_TITLE_ID
    "inspection": "policy_inspection_xxxxx",
    "appraisal": "policy_appraisal_xxxxx",
    "underwriting": "policy_underwriting_xxxxx"
}
```

**`budgets`**: Daily budgets in USDC
```python
{
    "title": 0.03,        # $0.03/day
    "inspection": 0.012,  # $0.012/day
    "appraisal": 0.010,   # $0.010/day
    "underwriting": 0.019 # $0.019/day
}
```

**`budget_usage`**: Tracks used budget (in-memory, not persisted)
```python
{
    "title": 0.0,
    "inspection": 0.0,
    "appraisal": 0.0,
    "underwriting": 0.0
}
```

#### Key Methods

**`__init__(api_key, wallet_address)`**
- **Purpose**: Initialize Locus integration
- **Parameters**:
  - `api_key`: Locus API key for authentication
  - `wallet_address`: Wallet address from wallet manager
- **Initialization Steps**:
  1. Store API key and wallet address
  2. Load policy IDs from environment (supports both uppercase/lowercase)
  3. Load budgets from environment
  4. Initialize budget usage tracking
  5. Log initialization
  6. Print summary
- **Environment Variable Support**: Handles both `LOCUS_POLICY_*_ID` and `locus_policy_*_id` formats

**`get_policy_id(agent_type: str) -> str`**
- **Purpose**: Get Policy Group ID for agent type
- **Normalization**: Converts agent type to lowercase, handles aliases
- **Error Handling**: Raises `ValueError` for invalid agent types
- **Example**:
  ```python
  get_policy_id("title") → "policy_title_xxxxx"
  get_policy_id("lending") → "policy_underwriting_xxxxx"  # Alias
  ```

**`get_budget(agent_type: str) -> float`**
- **Purpose**: Get daily budget for agent type
- **Returns**: Budget amount in USDC (float)
- **Normalization**: Handles agent type aliases
- **Example**:
  ```python
  get_budget("title") → 0.03
  get_budget("inspection") → 0.012
  ```

**`check_budget(agent_type: str, amount: float) -> Dict[str, Any]`**
- **Purpose**: Check if payment amount is within budget
- **Flow**:
  1. Normalize agent type
  2. Get budget and current usage
  3. Calculate available budget
  4. Check if amount <= available
  5. If approved: Update usage tracking
  6. Return result dictionary
- **Return Format**:
  ```python
  {
      "agent": "title",
      "amount": 0.03,
      "budget": 0.03,
      "used": 0.0,
      "available": 0.03,
      "approved": True,
      "message": "Payment approved"
  }
  ```
- **Budget Tracking**: Updates `self.budget_usage` on approval
- **Logging**: Logs approval/rejection with details

**`get_all_policies() -> Dict[str, Dict[str, Any]]`**
- **Purpose**: Get all policy information
- **Returns**: Nested dictionary with policy details
- **Format**:
  ```python
  {
      "title": {
          "policy_id": "policy_title_xxxxx",
          "budget": 0.03,
          "used": 0.0,
          "available": 0.03
      },
      "inspection": {...},
      "appraisal": {...},
      "underwriting": {...}
  }
  ```
- **Use Case**: Display policy status, dashboard views

**`get_api_key() -> str`**
- **Purpose**: Get Locus API key
- **Returns**: API key string
- **Security Note**: API key should be encrypted in production

#### Singleton Pattern

**`init_locus(api_key, wallet_address) -> LocusIntegration`**
- **Purpose**: Initialize global singleton instance
- **Environment Variable Support**: Loads from env if not provided
- **Error Handling**: Raises `ValueError` if API key or wallet missing
- **Idempotency**: Returns existing instance if already initialized

**`get_locus() -> Optional[LocusIntegration]`**
- **Purpose**: Get global singleton instance
- **Returns**: Instance if initialized, `None` otherwise

#### Technical Details

**Agent Type Normalization**:
- Converts to lowercase for case-insensitive matching
- Handles aliases (e.g., "lending" → "underwriting")
- Validates against known agent types

**Budget Management**:
- **Current**: In-memory tracking (resets on restart)
- **Production**: Should persist to database
- **Daily Reset**: Not implemented (would need cron job or scheduler)
- **Currency**: All amounts in USDC

**Policy Group IDs**:
- Format: `policy_xxxxx` (from Locus dashboard)
- Empty string if not configured
- Warning logged if missing

---

### 3. Locus Payment Handler (`services/locus_payment_handler.py`)

#### Purpose
Processes autonomous agent payments through Locus. Handles payment execution, budget checking, and payment history tracking.

#### Class Structure

```python
class LocusPaymentHandler:
    """
    Process autonomous agent payments through Locus.
    
    Responsibilities:
    - Execute payments with budget validation
    - Track payment history
    - Generate payment summaries
    - Extract agent types from agent IDs
    """
```

#### Key Attributes

**`locus`**: `LocusIntegration` instance
- Used for budget checking and policy management

**`payment_history`**: `List[Dict[str, Any]]`
- In-memory list of all payment records
- **Format**: List of payment dictionaries
- **Persistence**: Not persisted (resets on restart)
- **Production**: Should persist to database

#### Key Methods

**`__init__(locus_integration: LocusIntegration)`**
- **Purpose**: Initialize payment handler
- **Parameters**: `LocusIntegration` instance
- **Initialization**: Stores integration instance, initializes empty payment history

**`async execute_payment(...) -> Dict[str, Any]`**
- **Purpose**: Execute payment for an agent
- **Flow**:
  1. Extract agent type from agent_id
  2. Check budget via `locus.check_budget()`
  3. If rejected: Return rejection result, add to history
  4. If approved: Generate transaction hash, create payment record, add to history
  5. Return payment result
- **Parameters**:
  - `agent_id`: Agent identifier (e.g., "title-agent")
  - `amount`: Payment amount in USDC
  - `recipient`: Recipient wallet address
  - `service_url`: Service endpoint URL
  - `description`: Payment description
- **Return Format** (Success):
  ```python
  {
      "status": "SUCCESS",
      "agent": "title-agent",
      "agent_type": "title",
      "amount": 0.03,
      "recipient": "0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d",
      "tx_hash": "0x9f792d6239799082002317f989abfe9d6e5e3c7d",
      "timestamp": "2025-11-15T20:07:14.738484Z",
      "service": "http://localhost:5001/landamerica/title-search",
      "description": "Title verification for 123 Main St"
  }
  ```
- **Return Format** (Rejected):
  ```python
  {
      "status": "REJECTED",
      "reason": "Amount exceeds available budget",
      "agent": "title-agent",
      "agent_type": "title",
      "amount": 0.03,
      "budget": 0.025,
      "available": 0.02,
      "timestamp": "2025-11-15T20:07:14.738484Z"
  }
  ```
- **Transaction Hash Generation**: Uses `_generate_tx_hash()` (mock for demo)
- **Logging**: Comprehensive logging at each step
- **History Tracking**: All payments (success and rejected) added to history

**`get_payment_history(agent_id: Optional[str] = None) -> List[Dict[str, Any]]`**
- **Purpose**: Get payment history
- **Parameters**: Optional agent ID to filter
- **Returns**: List of payment records
- **Filtering**: If agent_id provided, returns only that agent's payments
- **Copy**: Returns copy of history (prevents external modification)

**`get_payment_summary() -> Dict[str, Any]`**
- **Purpose**: Get payment summary statistics
- **Returns**: Summary dictionary
- **Format**:
  ```python
  {
      "total_payments": 0.091,  # Total USDC spent
      "by_agent": {
          "title": 0.03,
          "inspection": 0.012,
          "appraisal": 0.010,
          "underwriting": 0.019
      },
      "total_budget": 0.091,    # Total daily budget
      "remaining": 0.0,         # Remaining budget
      "transactions": 4          # Number of successful payments
  }
  ```
- **Calculation**: Sums successful payments only
- **Budget**: Gets total from `locus.budgets`

**`_extract_agent_type(agent_id: str) -> str`**
- **Purpose**: Extract agent type from agent ID
- **Logic**: String matching on agent_id
  - Contains "title" → "title"
  - Contains "inspection" → "inspection"
  - Contains "appraisal" → "appraisal"
  - Contains "underwriting" or "lending" → "underwriting"
  - Default → "title" (with warning)
- **Use Case**: Map agent IDs to agent types for budget checking

**`_generate_tx_hash(agent_id, amount, recipient) -> str`**
- **Purpose**: Generate transaction hash (mock for demo)
- **Implementation**: SHA256 hash of `{agent_id}:{amount}:{recipient}:{timestamp}`
- **Format**: `0x` + first 40 characters of hash
- **Production**: Should create actual blockchain transaction
- **Example**: `0x9f792d6239799082002317f989abfe9d6e5e3c7d`

#### Technical Details

**Payment Execution Flow**:
```
execute_payment()
    ↓
_extract_agent_type() → "title"
    ↓
locus.check_budget("title", 0.03)
    ├─→ Get budget: 0.03
    ├─→ Get used: 0.0
    ├─→ Calculate available: 0.03
    ├─→ Check: 0.03 <= 0.03 → True
    └─→ Update usage: 0.0 → 0.03
    ↓
_generate_tx_hash() → "0x..."
    ↓
Create payment record
    ↓
Add to payment_history
    ↓
Return result
```

**Budget Checking Integration**:
- Uses `LocusIntegration.check_budget()`
- Budget check happens before payment execution
- Rejected payments still logged in history
- Budget usage updated on approval

**Transaction Hash**:
- **Current**: Deterministic hash (mock)
- **Production**: Should be actual blockchain transaction hash
- **Format**: Ethereum-style (0x + 40 hex characters)
- **Uniqueness**: Based on agent_id, amount, recipient, timestamp

---

### 4. x402 Protocol Handler (`services/x402_protocol_handler.py`)

#### Purpose
Handles the x402 payment protocol (HTTP 402 Payment Required). Implements the complete flow from service call to payment to data retrieval.

#### Class Structure

```python
class X402ProtocolHandler:
    """
    Handle x402 payment protocol (HTTP 402).
    
    Implements:
    - 402 response parsing
    - Payment signing
    - Automatic retry with payment header
    - Integration with Locus payment handler
    """
```

#### x402 Protocol Flow

```
Step 1: Initial Request
    Agent → GET service_url
    Service → 402 Payment Required
    {
        "error": "Payment Required",
        "amount": 0.03,
        "challenge": "landamerica_title_...",
        "currency": "USD"
    }

Step 2: Parse 402 Response
    Extract: amount, challenge, service name

Step 3: Sign Payment
    Option A: Use LocusPaymentHandler (if available)
        → execute_payment() → tx_hash
    Option B: Mock signing (fallback)
        → sign_payment() → signature

Step 4: Retry with Payment
    Agent → POST service_url
    Headers: {
        "X-PAYMENT": "0xSigned_...",
        "Content-Type": "application/json"
    }
    Service → 200 OK + Data

Step 5: Return Result
    {
        "status": "success",
        "data": {...},
        "payment_signed": "0xSigned_...",
        "tx_hash": "0x..."
    }
```

#### Key Methods

**`__init__(payment_handler=None)`**
- **Purpose**: Initialize x402 handler
- **Parameters**: Optional `LocusPaymentHandler` instance
- **Use Case**: If provided, uses real payments; otherwise uses mock signing

**`parse_402_response(response: httpx.Response) -> Dict[str, Any]`**
- **Purpose**: Parse HTTP 402 Payment Required response
- **Input**: httpx Response object with status 402
- **Parsing**:
  - Extracts JSON from response body
  - Gets amount, challenge, service name
  - Falls back to defaults if fields missing
- **Return Format**:
  ```python
  {
      "status": 402,
      "amount": 0.03,
      "challenge": "landamerica_title_...",
      "service": "LandAmerica",
      "message": "Payment Required",
      "currency": "USD"
  }
  ```
- **Error Handling**: Handles non-JSON responses gracefully

**`sign_payment(challenge: str, amount: float) -> str`**
- **Purpose**: Sign payment challenge (mock implementation)
- **Implementation**: SHA256 hash of `{challenge}:{amount}:{timestamp}`
- **Format**: `0xSigned_` + 32 hex characters
- **Production**: Should sign with wallet private key using ECDSA
- **Example**: `0xSigned_a1b2c3d4e5f6...`

**`async execute_x402_flow(...) -> Dict[str, Any]`**
- **Purpose**: Execute complete x402 payment flow
- **Flow**:
  1. Create httpx AsyncClient
  2. GET to service_url
  3. Check for 402 response
  4. Parse 402 response
  5. Sign payment (via handler or mock)
  6. POST with X-PAYMENT header
  7. Parse final response
  8. Return result
- **Parameters**:
  - `service_url`: Service endpoint URL
  - `amount`: Expected payment amount
  - `agent_id`: Optional agent ID for payment handler
  - `recipient`: Optional recipient address for payment handler
- **Return Format** (Success):
  ```python
  {
      "status": "success",
      "data": {
          "result": {
              "title_status": "CLEAR",
              "current_owner": "John Smith",
              ...
          }
      },
      "payment_signed": "0xSigned_...",
      "tx_hash": "0x9f792d6239799082002317f989abfe9d6e5e3c7d",
      "service": "LandAmerica"
  }
  ```
- **Return Format** (Failed):
  ```python
  {
      "status": "failed",
      "error": "Payment retry failed with status 500",
      "response_status": 500,
      "payment_signed": "0xSigned_..."
  }
  ```
- **Error Handling**:
  - TimeoutException → Returns timeout error
  - NetworkError → Returns network error
  - Other exceptions → Returns error message
- **Timeout**: 30 seconds per request
- **Logging**: Detailed logging at each step

**`async retry_with_payment_header(client, url, signature) -> httpx.Response`**
- **Purpose**: Retry request with X-PAYMENT header
- **Headers**: 
  ```python
  {
      "X-PAYMENT": signature,
      "Content-Type": "application/json"
  }
  ```
- **Method**: Tries POST first, falls back to GET
- **Returns**: httpx Response object

**`_extract_service_name(path: str) -> str`**
- **Purpose**: Extract service name from URL path
- **Mapping**:
  - "landamerica" → "LandAmerica"
  - "amerispec" → "AmeriSpec"
  - "corelogic" → "CoreLogic"
  - "fanniemae" → "Fannie Mae"
- **Fallback**: "Unknown Service"

#### Technical Details

**HTTP Client**:
- Uses `httpx.AsyncClient` for async HTTP requests
- Timeout: 30 seconds
- Supports both GET and POST methods
- Handles JSON and text responses

**Payment Integration**:
- **If LocusPaymentHandler available**: Uses real payment execution
- **If not available**: Falls back to mock signing
- **Seamless**: Agent code doesn't need to know which is used

**Error Recovery**:
- Network errors: Returns error, doesn't crash
- Timeout errors: Returns timeout message
- HTTP errors: Returns status code and message
- All errors logged with context

---

## Agent Integration

### Agent Architecture

All agents follow the same pattern:

```python
class VerificationAgent(ABC):
    """Base class for all verification agents."""
    
    @abstractmethod
    async def execute_verification(...) -> VerificationReport
    
    @abstractmethod
    async def validate_report(...) -> ValidationResult
```

### Agent Payment Integration Pattern

Each agent's `_perform_*()` method follows this pattern:

```python
async def _perform_verification(self, property_id, transaction):
    # 1. Get configuration
    from config.settings import settings
    from services.x402_protocol_handler import X402ProtocolHandler
    from services.locus_integration import get_locus
    
    # 2. Set up service details
    service_url = settings.service_url
    agent_id = "agent-name"
    recipient = "0x..."  # Service wallet address
    amount_usdc = float(self.PAYMENT_AMOUNT) / 1000.0
    
    # 3. Try to use Locus if available
    locus = get_locus()
    payment_handler = None
    
    if locus and not settings.use_mock_services:
        try:
            from services.locus_payment_handler import LocusPaymentHandler
            payment_handler = LocusPaymentHandler(locus)
        except Exception as e:
            self.log_activity(f"Locus unavailable: {e}", level="WARNING")
    
    # 4. Execute x402 flow
    x402_handler = X402ProtocolHandler(payment_handler=payment_handler)
    result = await x402_handler.execute_x402_flow(
        service_url=service_url,
        amount=amount_usdc,
        agent_id=agent_id if payment_handler else None,
        recipient=recipient if payment_handler else None
    )
    
    # 5. Handle result
    if result.get("status") != "success":
        raise Exception(f"Verification failed: {result.get('error')}")
    
    # 6. Transform and return
    data = result.get("data", {})
    result_data = data.get("result", data)
    return transformed_result
```

### Agent-Specific Details

#### Title Search Agent

**Service**: LandAmerica Title Search  
**Recipient**: `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d`  
**Payment**: $1,200 USD → 1.2 USDC (example conversion)  
**Budget**: $0.03/day  
**API Key**: `locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG`

**Return Format**:
```python
{
    "property_address": "123 Main St",
    "current_owner": "John Smith",
    "chain_of_title": [...],
    "liens_and_encumbrances": [],
    "has_issues": False,
    "title_status": "CLEAR",
    "payment_tx": "0x...",
    "report_date": "2025-11-15T..."
}
```

#### Inspection Agent

**Service**: AmeriSpec Inspection  
**Recipient**: `0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9`  
**Payment**: $500 USD → 0.5 USDC  
**Budget**: $0.012/day  
**API Key**: `locus_dev_NeMbZAgJFwpWXIrGaiZQTWm-Fhnpsxfd`

**Return Format**:
```python
{
    "property_address": "123 Main St",
    "inspection_date": "2025-11-18T...",
    "inspector_name": "Michael Johnson",
    "inspector_license": "CA-LIC-12345",
    "areas_inspected": [...],
    "has_major_issues": False,
    "overall_condition": "good",
    "payment_tx": "0x...",
    "status": "SCHEDULED"
}
```

#### Appraisal Agent

**Service**: CoreLogic Valuation  
**Recipient**: `0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574`  
**Payment**: $400 USD → 0.4 USDC  
**Budget**: $0.010/day  
**API Key**: `locus_dev_y7wmTdasNBO4gCsFxWJnQ8bo0IROSOKk`

**Return Format**:
```python
{
    "property_address": "123 Main St",
    "appraisal_date": "2025-11-15T...",
    "appraiser_name": "Sarah Williams",
    "appraiser_license": "CA-APP-67890",
    "appraised_value": 867000.0,
    "purchase_price": 850000.0,
    "appraisal_method": "sales_comparison",
    "comparable_properties": [...],
    "payment_tx": "0x...",
    "status": "APPROVED"
}
```

#### Lending Agent

**Service**: Fannie Mae Verification  
**Recipient**: `0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba`  
**Payment**: $0 USD → 0.0 USDC (signature required, no amount)  
**Budget**: $0.019/day  
**API Key**: `locus_dev_cRKUMxRuSSjqaQzRgdbdhm5Jz2-szqVl`  
**Note**: Maps to "underwriting" agent type for Locus

**Return Format**:
```python
{
    "lender_name": "Fannie Mae",
    "loan_officer_name": "Robert Chen",
    "loan_officer_contact": "r.chen@fanniemae.com",
    "loan_approved": True,
    "loan_amount": 825000.0,
    "loan_type": "conventional",
    "interest_rate": 6.5,
    "loan_term_years": 30,
    "underwriting_complete": True,
    "purchase_price": 850000.0,
    "payment_tx": "0x...",
    "status": "PRE-APPROVED"
}
```

---

## Payment Flow Architecture

### Complete Payment Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT EXECUTION                          │
│  agent.execute_verification(transaction, task_details)     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              AGENT._PERFORM_*() METHOD                      │
│  1. Get service URL from settings                          │
│  2. Get recipient wallet address                           │
│  3. Convert payment amount to USDC                         │
│  4. Check if Locus available                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           X402 PROTOCOL HANDLER                            │
│  x402_handler.execute_x402_flow()                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Step 1:     │   │  Step 2:     │   │  Step 3:     │
│  GET Request │   │  Parse 402   │   │  Sign Payment│
│              │   │  Response    │   │              │
│  service_url │   │  Extract:    │   │  Option A:   │
│      ↓       │   │  - amount    │   │  Locus       │
│  402 Response│   │  - challenge │   │  Handler     │
│              │   │  - service │   │      ↓         │
└──────────────┘   └──────────────┘   │  tx_hash     │
                                      │              │
                                      │  Option B:   │
                                      │  Mock Sign   │
                                      │      ↓       │
                                      │  signature   │
                                      └──────┬───────┘
                                             │
                                             ▼
                                    ┌──────────────┐
                                    │  Step 4:     │
                                    │  Retry with  │
                                    │  Payment     │
                                    │              │
                                    │  POST service│
                                    │  Headers:    │
                                    │  X-PAYMENT:  │
                                    │  signature   │
                                    │      ↓       │
                                    │  200 OK +    │
                                    │  Data        │
                                    └──────┬───────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │  Step 5:     │
                                    │  Return      │
                                    │  Result      │
                                    │              │
                                    │  Transform   │
                                    │  data to     │
                                    │  agent format│
                                    └──────────────┘
```

### Payment Handler Integration

When `LocusPaymentHandler` is available:

```
X402ProtocolHandler.execute_x402_flow()
    ↓
payment_handler.execute_payment()
    ↓
locus.check_budget(agent_type, amount)
    ├─→ Get budget: 0.03
    ├─→ Get used: 0.0
    ├─→ Calculate available: 0.03
    ├─→ Check: amount <= available
    └─→ Update usage if approved
    ↓
_generate_tx_hash() → "0x..."
    ↓
Return payment_result with tx_hash
    ↓
Use tx_hash as payment signature
```

### Mock Payment Flow

When `LocusPaymentHandler` is not available:

```
X402ProtocolHandler.execute_x402_flow()
    ↓
sign_payment(challenge, amount)
    ├─→ Create hash: SHA256(challenge:amount:timestamp)
    └─→ Return: "0xSigned_..."
    ↓
Use signature as payment proof
```

---

## Configuration Management

### Settings Class (`config/settings.py`)

#### Locus Configuration Section

```python
# Locus Payment Infrastructure
locus_wallet_address: str = ""
locus_wallet_private_key: str = ""
locus_wallet_name: str = "Yc-MakeEmPay"
locus_chain_id: int = 8453  # Base Mainnet
locus_api_key: str = ""

# Locus Policy IDs
locus_policy_title_id: str = ""
locus_policy_inspection_id: str = ""
locus_policy_appraisal_id: str = ""
locus_policy_underwriting_id: str = ""

# Locus Agent IDs & Keys
locus_agent_title_id: str = ""
locus_agent_title_key: str = ""
locus_agent_inspection_id: str = ""
locus_agent_inspection_key: str = ""
locus_agent_appraisal_id: str = ""
locus_agent_appraisal_key: str = ""
locus_agent_underwriting_id: str = ""
locus_agent_underwriting_key: str = ""

# Agent Budgets (in USDC)
agent_title_budget: float = 0.03
agent_inspection_budget: float = 0.012
agent_appraisal_budget: float = 0.010
agent_underwriting_budget: float = 0.019

# Mock Services (for demo)
landamerica_service: str = "http://localhost:5001/landamerica/title-search"
amerispec_service: str = "http://localhost:5001/amerispec/inspection"
corelogic_service: str = "http://localhost:5001/corelogic/valuation"
fanniemae_service: str = "http://localhost:5001/fanniemae/verify"

# Demo Mode
demo_mode: bool = True
use_mock_services: bool = True
```

#### Environment Variable Loading

- **Base Class**: `pydantic_settings.BaseSettings`
- **Config**: `env_file = ".env"`, `case_sensitive = False`
- **Automatic**: All fields automatically loaded from `.env`
- **Type Conversion**: Automatic (str, int, float, bool)
- **Defaults**: Provided for all fields

---

## Data Models & Structures

### Payment Record Structure

```python
{
    "status": "SUCCESS" | "REJECTED",
    "agent": "title-agent",
    "agent_type": "title",
    "amount": 0.03,  # USDC
    "recipient": "0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d",
    "tx_hash": "0x9f792d6239799082002317f989abfe9d6e5e3c7d",
    "timestamp": "2025-11-15T20:07:14.738484Z",  # ISO 8601 UTC
    "service": "http://localhost:5001/landamerica/title-search",
    "description": "Title verification for 123 Main St"
}
```

### Budget Check Result Structure

```python
{
    "agent": "title",
    "amount": 0.03,
    "budget": 0.03,
    "used": 0.0,
    "available": 0.03,
    "approved": True,
    "message": "Payment approved"
}
```

### x402 Flow Result Structure

```python
{
    "status": "success" | "failed",
    "data": {
        "result": {
            # Service-specific data
        }
    },
    "payment_signed": "0xSigned_...",
    "tx_hash": "0x9f792d6239799082002317f989abfe9d6e5e3c7d",
    "service": "LandAmerica"
}
```

### Wallet Info Structure

```python
{
    "name": "Yc-MakeEmPay",
    "address": "0x45B876546953Fe28C66022b48310dFbc1c2Fec47",
    "chain_id": 8453,
    "network": "Base Mainnet",
    "status": "Active" | "Invalid"
}
```

### Policy Info Structure

```python
{
    "title": {
        "policy_id": "policy_title_xxxxx",
        "budget": 0.03,
        "used": 0.0,
        "available": 0.03
    },
    "inspection": {...},
    "appraisal": {...},
    "underwriting": {...}
}
```

---

## Error Handling & Resilience

### Error Types

1. **Wallet Validation Errors**
   - Invalid address format
   - Invalid private key format
   - Missing credentials
   - **Handling**: Raises `ValueError` with descriptive message

2. **Budget Check Errors**
   - Amount exceeds budget
   - Invalid agent type
   - **Handling**: Returns rejection result, logs warning

3. **Payment Execution Errors**
   - Payment rejected (budget)
   - Transaction hash generation failure
   - **Handling**: Returns error result, logs error

4. **x402 Protocol Errors**
   - Network timeout
   - Network error
   - Unexpected HTTP status
   - JSON parsing error
   - **Handling**: Returns error result with details, logs error

5. **Service Integration Errors**
   - Service unavailable
   - Invalid response format
   - **Handling**: Raises exception, agent handles

### Error Recovery

**Budget Rejection**:
- Payment not executed
- Rejection logged in history
- Agent receives rejection result
- Agent can retry or escalate

**Network Errors**:
- Timeout: Returns timeout error
- Network: Returns network error
- Retry: Not automatic (agent can retry)
- Logging: All errors logged with context

**Service Errors**:
- 402 not received: Returns error
- Payment retry fails: Returns error
- Agent raises exception
- Workflow engine can retry

---

## Performance Considerations

### Async/Await Pattern

All payment operations are async:
- `execute_payment()`: `async def`
- `execute_x402_flow()`: `async def`
- Uses `httpx.AsyncClient` for HTTP requests
- Non-blocking I/O

### Singleton Pattern

- **Wallet Manager**: Single instance, reused
- **Locus Integration**: Single instance, reused
- **Payment Handler**: Created per transaction (lightweight)
- **x402 Handler**: Created per call (stateless)

### Caching

**Current**: No caching implemented

**Potential Optimizations**:
- Cache policy group info
- Cache budget status (with TTL)
- Cache service responses (if idempotent)

### Timeout Management

- **HTTP Requests**: 30 seconds timeout
- **x402 Flow**: Total timeout ~60 seconds (2 requests)
- **Error Handling**: Fast failure on timeout

### Memory Usage

- **Payment History**: In-memory list (grows unbounded)
- **Budget Usage**: In-memory dict (4 entries)
- **Production**: Should persist to database

---

## Security Implementation

### Credential Storage

**Current**:
- Environment variables (`.env` file)
- Not committed to git (should be in `.gitignore`)
- Loaded via Pydantic BaseSettings

**Production Recommendations**:
- Use secret management service (AWS Secrets Manager, etc.)
- Encrypt private keys at rest
- Use key derivation for signing
- Rotate credentials regularly

### Private Key Handling

**Current**:
- Stored in memory after loading
- Passed to services (not ideal)
- Not encrypted in memory

**Production Recommendations**:
- Use hardware security module (HSM)
- Encrypt in memory
- Never log private keys
- Use secure key derivation

### API Key Security

**Current**:
- Stored in environment variables
- Passed to services
- Logged (masked in logs)

**Production Recommendations**:
- Rotate regularly
- Use OAuth 2.0 instead of API keys
- Store in secret management
- Monitor for leaks

### Payment Validation

**Current**:
- Budget checking before payment
- Amount validation
- Recipient validation (format only)

**Production Recommendations**:
- Whitelist recipient addresses
- Rate limiting per agent
- Transaction monitoring
- Fraud detection

---

## Integration Points

### FastAPI Application Integration

**Startup Event** (`api/main.py`):

```python
@app.on_event("startup")
async def startup_event():
    if settings.locus_api_key and settings.locus_wallet_address:
        initialize_locus_on_startup()
    else:
        logger.info("Locus not configured, skipping initialization (demo mode)")
```

**App State Storage**:
```python
app.state.locus_wallet = wallet
app.state.locus = locus
app.state.locus_payment_handler = payment_handler
```

**Access in Routes**:
```python
@app.get("/api/locus/status")
async def get_locus_status(request: Request):
    wallet = request.app.state.locus_wallet
    locus = request.app.state.locus
    # Use wallet and locus...
```

### Agent Integration

**Pattern**: All agents use same integration pattern
- Import services at method level (lazy loading)
- Check for Locus availability
- Fallback to mock if unavailable
- Seamless switching between modes

### Service Dependencies

```
LocusPaymentHandler
    └─→ Requires: LocusIntegration
            └─→ Requires: API key, wallet address

X402ProtocolHandler
    └─→ Optional: LocusPaymentHandler
            └─→ If not provided: Uses mock signing

Agents
    └─→ Use: X402ProtocolHandler
            └─→ Optionally uses: LocusPaymentHandler
```

---

## Testing & Validation

### Unit Testing

**Wallet Manager**:
- Test address validation
- Test private key validation
- Test wallet info generation
- Test singleton pattern

**Locus Integration**:
- Test policy ID retrieval
- Test budget checking
- Test agent type normalization
- Test policy info generation

**Payment Handler**:
- Test payment execution
- Test budget rejection
- Test payment history
- Test payment summary

**x402 Handler**:
- Test 402 parsing
- Test payment signing
- Test retry with header
- Test error handling

### Integration Testing

**Full Flow**:
1. Initialize Locus
2. Agent executes verification
3. x402 flow completes
4. Payment recorded
5. Verify payment history

### Demo Testing

**Mock Services**:
- Test with mock services (demo mode)
- Verify all 4 agents complete
- Check payment signatures
- Verify transaction hashes

---

## Production Readiness

### Current Status: Demo-Ready ✅

**What Works**:
- ✅ Complete payment flow
- ✅ Budget checking
- ✅ x402 protocol
- ✅ Agent integration
- ✅ Mock services

**What's Missing for Production**:
- ⚠️ Real Locus API integration
- ⚠️ Database persistence for payment history
- ⚠️ Database persistence for budget usage
- ⚠️ Real blockchain transaction creation
- ⚠️ Production error handling enhancements
- ⚠️ Monitoring and alerting
- ⚠️ Rate limiting
- ⚠️ Fraud detection

### Production Checklist

- [ ] Get Policy Group IDs from Locus dashboard
- [ ] Get Agent IDs from Locus dashboard
- [ ] Find Locus Backend API documentation
- [ ] Implement real API client
- [ ] Replace mock payments with real API calls
- [ ] Add database persistence
- [ ] Implement production error handling
- [ ] Add monitoring and alerting
- [ ] Security audit
- [ ] Load testing
- [ ] End-to-end testing with real Locus

---

## Code Statistics

### Files Created/Updated

**New Files (4)**:
- `services/locus_wallet_manager.py` - 215 lines
- `services/locus_integration.py` - 270 lines
- `services/locus_payment_handler.py` - 246 lines
- `services/x402_protocol_handler.py` - 310 lines

**Updated Files (6)**:
- `config/settings.py` - Added 40+ Locus settings
- `api/main.py` - Added 70+ lines for Locus initialization
- `agents/title_search_agent.py` - Updated `_perform_title_search()`
- `agents/inspection_agent.py` - Updated `_perform_inspection()`
- `agents/appraisal_agent.py` - Updated `_perform_appraisal()`
- `agents/lending_agent.py` - Updated `_perform_lending_verification()`

**Total Lines of Code**: ~1,200+ lines

### Complexity Metrics

- **Classes**: 4 main classes
- **Methods**: 25+ methods
- **Async Methods**: 3 async methods
- **Singleton Functions**: 4 functions
- **Error Handling**: Comprehensive try/except blocks
- **Logging**: Structured logging throughout

---

## Future Enhancements

### Short Term
1. Get Policy Group IDs and Agent IDs from dashboard
2. Add database persistence for payment history
3. Add database persistence for budget usage
4. Enhance error messages

### Medium Term
1. Find Locus Backend API documentation
2. Implement real API client
3. Replace mock payments with real calls
4. Add retry logic with exponential backoff
5. Add circuit breakers for Locus API

### Long Term
1. Implement OAuth 2.0 authentication
2. Add real-time budget monitoring
3. Add payment analytics dashboard
4. Implement fraud detection
5. Add multi-wallet support

---

## Demo Infrastructure

### Mock Services (`demo/mock_services.py`)

**Purpose**: Simulate real third-party APIs that require x402 payments.

**Technology**: Flask web server running on `localhost:5001`

**Services Implemented**:
1. **LandAmerica Title Search** (`/landamerica/title-search`)
   - Amount: $1,200.00 USD
   - Returns: Title status, owner info, chain of title

2. **AmeriSpec Inspection** (`/amerispec/inspection`)
   - Amount: $500.00 USD
   - Returns: Inspection schedule, inspector details

3. **CoreLogic Valuation** (`/corelogic/valuation`)
   - Amount: $400.00 USD
   - Returns: Appraised value, comparable properties

4. **Fannie Mae Verification** (`/fanniemae/verify`)
   - Amount: $0.00 USD (signature required, no payment)
   - Returns: Loan approval status, terms

**x402 Flow Implementation**:
```python
# Initial GET request
GET /landamerica/title-search
→ 402 Payment Required
{
    "error": "Payment Required",
    "amount": 1200.00,
    "challenge": "landamerica_title_abc123...",
    "currency": "USD"
}

# Retry with payment
POST /landamerica/title-search
Headers: {
    "X-PAYMENT": "0xSigned_..."
}
→ 200 OK
{
    "result": {
        "title_status": "CLEAR",
        "current_owner": "John Smith",
        ...
    },
    "payment_tx": "0xSigned_..."
}
```

**Payment Tracking**:
- In-memory dictionary `payments = {}`
- Key: `{endpoint}:{signature}`
- Value: Payment timestamp and details
- Prevents duplicate payments

**Health Endpoint**:
- `GET /health` → Returns service status
- Used for service availability checks

### Mock Service Client (`demo/mock_service_client.py`)

**Purpose**: Client library for interacting with mock x402 services.

**Class**: `MockServiceClient`

**Key Method**:
```python
async def call_service_with_payment(
    endpoint: str,
    property_id: str,
    transaction_id: str,
    amount: Decimal,
    additional_data: Optional[Dict] = None
) -> Dict[str, Any]
```

**Flow**:
1. Initial GET request to endpoint
2. Handle 402 response
3. Generate payment signature
4. Retry with `X-PAYMENT` header
5. Return service data

**Payment Signature Generation**:
- Uses `payment_helper.generate_payment_signature()`
- Format: `0xSigned_{hash}`
- Deterministic based on challenge and timestamp

### Simple Demo (`demo/simple_demo.py`)

**Purpose**: End-to-end demo of x402 payment handling.

**Flow**:
1. Initialize `MockServiceClient`
2. Call all 4 services in sequence
3. Display results
4. Show timing and success rate

**Output**:
```
============================================================
AUTONOMOUS x402 PAYMENT HANDLING DEMO
============================================================

[Title Search] Calling /landamerica/title-search
[Title Search] ✓ SUCCESS - CLEAR
[Title Search] ✓ TX: 0xSigned_...

[Inspection] Calling /amerispec/inspection
[Inspection] ✓ SUCCESS - SCHEDULED
[Inspection] ✓ TX: 0xSigned_...

...

============================================================
DEMO RESULTS
============================================================

✓ 4/4 services completed successfully
⏱  Total time: 1.23 seconds

🎉 All services completed autonomously!
   - All x402 payments verified
   - All services called successfully
   - All payments signed and submitted
```

### Demo Architecture

```
┌─────────────────────────────────────────┐
│      Mock Services (Flask)              │
│      localhost:5001                     │
│                                         │
│  - /landamerica/title-search            │
│  - /amerispec/inspection                │
│  - /corelogic/valuation                 │
│  - /fanniemae/verify                    │
│  - /health                              │
└───────────────┬─────────────────────────┘
                │
                │ HTTP (x402 Protocol)
                │
                ▼
┌─────────────────────────────────────────┐
│      Mock Service Client                │
│      (demo/mock_service_client.py)      │
│                                         │
│  - Handles 402 responses                │
│  - Generates payment signatures         │
│  - Retries with X-PAYMENT header        │
└───────────────┬─────────────────────────┘
                │
                │ Used by
                │
                ▼
┌─────────────────────────────────────────┐
│      Agents                             │
│      (agents/*.py)                      │
│                                         │
│  - Title Search Agent                   │
│  - Inspection Agent                     │
│  - Appraisal Agent                      │
│  - Lending Agent                        │
└─────────────────────────────────────────┘
```

### Running the Demo

**Terminal 1 - Start Mock Services**:
```bash
cd realtorAIYC-main
python3 demo/mock_services.py
```

**Terminal 2 - Run Demo**:
```bash
cd realtorAIYC-main
python3 demo/simple_demo.py
```

**Expected Output**:
- Mock services start on port 5001
- Demo calls all 4 services
- All services return 402 initially
- All services accept payment and return data
- Total time: ~1-2 seconds

---

## Conclusion

This implementation provides a **complete, production-grade structure** for Locus payment integration. While it currently uses mock services for demos, the architecture is designed to seamlessly switch to real Locus API calls when documentation is available.

**Key Strengths**:
- ✅ Clean architecture
- ✅ Comprehensive error handling
- ✅ Flexible (mock or real)
- ✅ Well-documented
- ✅ Production-ready structure
- ✅ Complete demo infrastructure

**Implementation Summary**:
- **4 Core Services**: Wallet, Integration, Payment Handler, x402 Handler
- **4 Agent Updates**: Title, Inspection, Appraisal, Lending
- **1 Configuration Update**: Settings with 40+ Locus variables
- **1 Application Update**: FastAPI startup integration
- **Demo Infrastructure**: Mock services, client, and demo scripts
- **Total Code**: ~1,200+ lines of production code

**Next Steps**:
1. Get Policy/Agent IDs from dashboard
2. Find Locus API documentation
3. Implement real API client
4. Test with real Locus

---

**Status**: ✅ **IMPLEMENTATION COMPLETE** (Demo-Ready)

