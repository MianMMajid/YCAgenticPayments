# Required APIs for Escrow Agents Completion

This document lists all specific APIs needed to complete the three remaining integration tasks.

---

## 1. Real API Integrations (Medium Priority)

### 1.1 Title Search Agent API

**Current Status**: Uses mock implementation  
**File**: `agents/title_search_agent.py:62` - `# Mock title search - in production, this would integrate with title company APIs`

#### Required API Options:

**Option A: First American Title API** (Recommended)
- **Website**: https://www.firstam.com/developers
- **API Documentation**: https://developer.firstam.com/
- **What You Need**:
  - API Key/Client ID
  - Client Secret
  - Account credentials
- **Endpoints Needed**:
  - `POST /title-orders` - Create title order
  - `GET /title-orders/{id}` - Get title search status
  - `GET /title-orders/{id}/report` - Download title report
  - `GET /title-orders/{id}/chain-of-title` - Get chain of title
  - `GET /title-orders/{id}/liens` - Get liens and encumbrances
- **Cost**: Contact for pricing (typically $50-200 per title search)
- **Integration Code Location**: `agents/title_search_agent.py:_perform_title_search()`

**Option B: Fidelity National Title API**
- **Website**: https://www.fntic.com/
- **API Access**: Contact sales for API access
- **What You Need**:
  - API credentials
  - Account setup
- **Endpoints Needed**:
  - Title search initiation
  - Report retrieval
  - Lien/encumbrance data
- **Cost**: Contact for pricing

**Option C: Stewart Title API**
- **Website**: https://www.stewart.com/
- **API Access**: Contact for developer access
- **What You Need**:
  - API credentials
  - Integration agreement
- **Cost**: Contact for pricing

**Option D: Title API (Third-Party Aggregator)**
- **Services**: 
  - TitleAPI.com
  - TitleVest API
  - PropertyRadar API
- **Pros**: Easier integration, standardized API
- **Cons**: May be more expensive
- **Cost**: $100-300 per search

#### Implementation Requirements:

```python
# services/title_company_client.py (NEW FILE NEEDED)
class TitleCompanyClient:
    async def initiate_title_search(
        self,
        property_address: str,
        property_id: str
    ) -> str:  # Returns order_id
    
    async def get_title_search_status(
        self,
        order_id: str
    ) -> Dict[str, Any]:  # Returns status, report_url
    
    async def get_title_report(
        self,
        order_id: str
    ) -> Dict[str, Any]:  # Returns full title report
```

**Environment Variable Needed**:
```bash
TITLE_COMPANY_API_KEY=your_api_key
TITLE_COMPANY_API_URL=https://api.titlecompany.com/v1
```

---

### 1.2 Inspection Agent API

**Current Status**: Uses mock implementation  
**File**: `agents/inspection_agent.py:62` - `# Mock inspection - in production, this would integrate with inspection service APIs`

#### Required API Options:

**Option A: HomeAdvisor API** (Recommended)
- **Website**: https://www.homeadvisor.com/developers/
- **API Documentation**: Contact for API access
- **What You Need**:
  - API Key
  - Partner account
  - Business verification
- **Endpoints Needed**:
  - `POST /inspections/request` - Request inspection
  - `GET /inspections/{id}/status` - Check inspection status
  - `GET /inspections/{id}/report` - Get inspection report
  - `GET /inspectors/available` - Find available inspectors
- **Cost**: Typically $50-150 per inspection booking
- **Integration Code Location**: `agents/inspection_agent.py:_perform_inspection()`

**Option B: Thumbtack Pro API**
- **Website**: https://www.thumbtack.com/pro/
- **API Access**: Contact for Pro API access
- **What You Need**:
  - Pro account
  - API credentials
- **Endpoints Needed**:
  - Inspector search/booking
  - Inspection scheduling
  - Report retrieval
- **Cost**: Commission-based (typically 15-20% of service cost)

**Option C: Porch Pro API**
- **Website**: https://pro.porch.com/
- **API Access**: Contact for API access
- **What You Need**:
  - Pro account
  - API credentials
- **Cost**: Commission-based

**Option D: Custom Inspector Marketplace**
- **Build Your Own**: Create marketplace of certified inspectors
- **Pros**: Full control, direct relationships
- **Cons**: Requires building inspector network
- **Cost**: Development time + inspector recruitment

**Option E: Inspector Network APIs**
- **Services**:
  - InterNACHI API (International Association of Certified Home Inspectors)
  - ASHI API (American Society of Home Inspectors)
- **What You Need**:
  - Membership/partnership
  - API credentials
- **Cost**: Membership fees + per-inspection fees

#### Implementation Requirements:

```python
# services/inspection_client.py (NEW FILE NEEDED)
class InspectionClient:
    async def find_available_inspectors(
        self,
        property_address: str,
        requested_date: datetime
    ) -> List[Dict[str, Any]]:  # Returns list of available inspectors
    
    async def book_inspection(
        self,
        inspector_id: str,
        property_address: str,
        scheduled_time: datetime
    ) -> str:  # Returns booking_id
    
    async def get_inspection_status(
        self,
        booking_id: str
    ) -> Dict[str, Any]:  # Returns status, completion date
    
    async def get_inspection_report(
        self,
        booking_id: str
    ) -> Dict[str, Any]:  # Returns full inspection report
```

**Environment Variable Needed**:
```bash
INSPECTION_SERVICE_API_KEY=your_api_key
INSPECTION_SERVICE_API_URL=https://api.inspectionservice.com/v1
```

---

### 1.3 Appraisal Agent API

**Current Status**: Uses mock implementation  
**File**: `agents/appraisal_agent.py:65` - `# Mock appraisal - in production, this would integrate with appraisal service APIs`

#### Required API Options:

**Option A: Appraisal Management Company (AMC) APIs** (Recommended)
- **Major AMCs**:
  - **AppraisalPort API**: https://www.appraisalport.com/
  - **AppraisalScope API**: https://www.appraisalscope.com/
  - **LenderX API**: https://www.lenderx.com/
  - **Clear Capital API**: https://www.clearcapital.com/
- **What You Need**:
  - AMC account
  - API credentials
  - Business license/credentials
- **Endpoints Needed**:
  - `POST /appraisals/order` - Order appraisal
  - `GET /appraisals/{id}/status` - Check appraisal status
  - `GET /appraisals/{id}/report` - Get appraisal report
  - `GET /appraisers/available` - Find available appraisers
- **Cost**: Typically $300-600 per appraisal
- **Integration Code Location**: `agents/appraisal_agent.py:_perform_appraisal()`

**Option B: Automated Valuation Model (AVM) APIs**
- **Services**:
  - **CoreLogic AVM API**: https://www.corelogic.com/
  - **Black Knight AVM API**: https://www.blackknightinc.com/
  - **Chase AVM API**: https://developer.chase.com/
- **Pros**: Faster, cheaper
- **Cons**: Less accurate, may not meet lender requirements
- **Cost**: $10-50 per valuation
- **Note**: May need full appraisal for lender approval

**Option C: Real Estate Data APIs with Appraisal**
- **Services**:
  - **RentCast API** (already integrated) - Has AVM but not full appraisal
  - **Zillow Zestimate API** - Property value estimates
  - **Redfin API** - Property valuations
- **Pros**: Already have RentCast
- **Cons**: Not full appraisals, may not meet lender requirements

**Option D: Direct Appraiser Network**
- **Build Your Own**: Create network of certified appraisers
- **Pros**: Full control, direct relationships
- **Cons**: Requires building appraiser network, licensing requirements
- **Cost**: Development time + appraiser recruitment

#### Implementation Requirements:

```python
# services/appraisal_client.py (NEW FILE NEEDED)
class AppraisalClient:
    async def order_appraisal(
        self,
        property_address: str,
        property_id: str,
        purchase_price: Decimal,
        loan_amount: Decimal
    ) -> str:  # Returns order_id
    
    async def get_appraisal_status(
        self,
        order_id: str
    ) -> Dict[str, Any]:  # Returns status, estimated_completion
    
    async def get_appraisal_report(
        self,
        order_id: str
    ) -> Dict[str, Any]:  # Returns full appraisal report with value
```

**Environment Variable Needed**:
```bash
APPRAISAL_SERVICE_API_KEY=your_api_key
APPRAISAL_SERVICE_API_URL=https://api.appraisalservice.com/v1
```

---

### 1.4 Lending Agent API

**Current Status**: Uses mock implementation  
**File**: `agents/lending_agent.py` - Mock lending verification

#### Required API Options:

**Option A: Lender-Specific APIs** (Most Common)
- **Major Lenders with APIs**:
  - **Rocket Mortgage API**: https://developer.rocketmortgage.com/
  - **Quicken Loans API**: Contact for access
  - **Wells Fargo Mortgage API**: Contact for partnership
  - **Chase Mortgage API**: https://developer.chase.com/
  - **Bank of America Mortgage API**: Contact for access
- **What You Need**:
  - Lender partnership/account
  - API credentials
  - Business verification
- **Endpoints Needed**:
  - `GET /loans/{loan_id}/status` - Check loan status
  - `GET /loans/{loan_id}/underwriting` - Get underwriting status
  - `GET /loans/{loan_id}/commitment` - Get loan commitment letter
  - `POST /loans/{loan_id}/verify` - Verify loan conditions
- **Cost**: Typically free (part of loan process)
- **Integration Code Location**: `agents/lending_agent.py:_verify_loan_status()`

**Option A: Mortgage Broker APIs**
- **Services**:
  - **MortgageHippo API**: https://www.mortgagehippo.com/
  - **Better.com API**: https://www.better.com/developers
  - **LendingTree API**: Contact for access
- **What You Need**:
  - Broker account
  - API credentials
- **Cost**: Commission-based

**Option C: Underwriting System APIs**
- **Services**:
  - **Encompass API** (Ellie Mae): https://www.elliemae.com/
  - **Calyx Point API**: https://www.calyxsoftware.com/
  - **Byte API**: https://www.bytepro.com/
- **What You Need**:
  - System license
  - API credentials
- **Cost**: Software licensing fees

**Option D: Credit/Loan Verification APIs**
- **Services**:
  - **Experian Credit API**: https://developer.experian.com/
  - **Equifax Credit API**: https://developer.equifax.com/
  - **TransUnion Credit API**: https://developer.transunion.com/
- **What You Need**:
  - Credit bureau account
  - API credentials
  - Compliance requirements (FCRA)
- **Cost**: $0.50-2.00 per credit check
- **Note**: Only provides credit data, not full loan status

#### Implementation Requirements:

```python
# services/lending_client.py (NEW FILE NEEDED)
class LendingClient:
    async def verify_loan_status(
        self,
        loan_id: str,
        borrower_id: str
    ) -> Dict[str, Any]:  # Returns loan status, approval status
    
    async def get_underwriting_status(
        self,
        loan_id: str
    ) -> Dict[str, Any]:  # Returns underwriting completion status
    
    async def get_loan_commitment(
        self,
        loan_id: str
    ) -> Dict[str, Any]:  # Returns commitment letter, conditions
```

**Environment Variable Needed**:
```bash
LENDER_API_KEY=your_api_key
LENDER_API_URL=https://api.lender.com/v1
# OR for multiple lenders:
ROCKET_MORTGAGE_API_KEY=...
CHASE_MORTGAGE_API_KEY=...
```

---

## 2. Stripe API Integration (HIGH PRIORITY - Currently Not Implemented)

**Current Status**: ⚠️ **NOT IMPLEMENTED** - Placeholder code only  
**File**: `services/agentic_stripe_client.py` - All methods raise `NotImplementedError`

### Critical Finding

The codebase references "Agentic Stripe" which **does not exist**. You need to implement **actual Stripe API integration** using:
- **Stripe Connect** (for multi-party escrow payments)
- **Payment Intents** (for holding earnest money)
- **Transfers/Payouts** (for milestone payments and settlements)

### Required Stripe APIs:

**Stripe Connect API** (Essential for Escrow)
- **Website**: https://stripe.com/connect
- **API Documentation**: https://docs.stripe.com/connect
- **What You Need**:
  - Stripe account (https://dashboard.stripe.com/)
  - API keys (Publishable and Secret keys)
  - Connect account setup
  - Webhook endpoint configured
- **Cost**: 2.9% + $0.30 per transaction (standard Stripe fees)
- **Connect Fees**: Additional 0.25% for platform (optional)

**Key Stripe Features Needed:**

1. **Payment Intents API** (For Earnest Money Deposits)
   - **Endpoint**: `POST /v1/payment_intents`
   - **Purpose**: Create payment intent to hold earnest money
   - **Documentation**: https://docs.stripe.com/api/payment_intents
   - **Implementation**: Replace `create_wallet()` method

2. **Stripe Connect Accounts** (For Multi-Party Payments)
   - **Endpoint**: `POST /v1/accounts` (Connect accounts)
   - **Purpose**: Create connected accounts for sellers, agents, service providers
   - **Documentation**: https://docs.stripe.com/connect/accounts
   - **Implementation**: For milestone payments to inspectors, appraisers, etc.

3. **Transfers API** (For Milestone Payments)
   - **Endpoint**: `POST /v1/transfers`
   - **Purpose**: Transfer funds to connected accounts (service providers)
   - **Documentation**: https://docs.stripe.com/connect/charges-transfers
   - **Implementation**: Replace `release_milestone_payment()` method

4. **Payouts API** (For Final Settlement)
   - **Endpoint**: `POST /v1/payouts`
   - **Purpose**: Distribute funds to multiple parties (seller, agents, closing costs)
   - **Documentation**: https://docs.stripe.com/api/payouts
   - **Implementation**: Replace `execute_final_settlement()` method

5. **Balance API** (For Wallet Balance)
   - **Endpoint**: `GET /v1/balance`
   - **Purpose**: Check available balance in Stripe account
   - **Documentation**: https://docs.stripe.com/api/balance
   - **Implementation**: Replace `get_wallet_balance()` method

6. **Webhooks** (For Payment Status Updates)
   - **Events**: `payment_intent.succeeded`, `transfer.created`, `payout.paid`
   - **Purpose**: Real-time payment status updates
   - **Documentation**: https://docs.stripe.com/webhooks
   - **Implementation**: Replace `verify_webhook_signature()` method

### Implementation Requirements:

```python
# services/stripe_client.py (REPLACE agentic_stripe_client.py)
import stripe
from decimal import Decimal
from typing import Dict, Any, List

class StripeClient:
    def __init__(self, api_key: str, webhook_secret: str):
        """Initialize Stripe client."""
        stripe.api_key = api_key
        self.webhook_secret = webhook_secret
    
    async def create_escrow_payment_intent(
        self,
        transaction_id: str,
        amount: Decimal,
        currency: str = "usd"
    ) -> Dict[str, Any]:
        """Create payment intent for earnest money deposit."""
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            metadata={
                "transaction_id": transaction_id,
                "type": "earnest_money"
            },
            capture_method="manual"  # Hold funds, don't capture immediately
        )
        return {
            "payment_intent_id": intent.id,
            "client_secret": intent.client_secret,
            "status": intent.status
        }
    
    async def create_connected_account(
        self,
        account_type: str = "express",
        email: str = None
    ) -> Dict[str, Any]:
        """Create Stripe Connect account for service provider."""
        account = stripe.Account.create(
            type=account_type,
            email=email,
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True}
            }
        )
        return {
            "account_id": account.id,
            "account_type": account.type
        }
    
    async def release_milestone_payment(
        self,
        payment_intent_id: str,
        connected_account_id: str,
        amount: Decimal,
        currency: str = "usd"
    ) -> Dict[str, Any]:
        """Release payment to connected account (service provider)."""
        # First, capture the payment intent
        intent = stripe.PaymentIntent.capture(payment_intent_id)
        
        # Then transfer to connected account
        transfer = stripe.Transfer.create(
            amount=int(amount * 100),
            currency=currency,
            destination=connected_account_id,
            metadata={
                "payment_intent_id": payment_intent_id,
                "type": "milestone_payment"
            }
        )
        return {
            "transfer_id": transfer.id,
            "payment_intent_id": intent.id,
            "status": transfer.status
        }
    
    async def execute_settlement(
        self,
        payment_intent_id: str,
        distributions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute final settlement with multiple distributions."""
        # Capture the payment intent
        intent = stripe.PaymentIntent.capture(payment_intent_id)
        
        # Create transfers for each distribution
        transfers = []
        for dist in distributions:
            transfer = stripe.Transfer.create(
                amount=int(dist["amount"] * 100),
                currency=dist.get("currency", "usd"),
                destination=dist["account_id"],
                metadata={
                    "transaction_id": dist.get("transaction_id"),
                    "type": dist.get("type", "settlement")
                }
            )
            transfers.append(transfer)
        
        return {
            "payment_intent_id": intent.id,
            "transfers": [t.id for t in transfers],
            "status": "completed"
        }
    
    async def get_balance(self) -> Decimal:
        """Get available balance."""
        balance = stripe.Balance.retrieve()
        return Decimal(balance.available[0].amount) / 100
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
        """Verify webhook signature."""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return True
        except ValueError:
            return False
        except stripe.error.SignatureVerificationError:
            return False
```

**Environment Variables Needed**:
```bash
STRIPE_SECRET_KEY=sk_test_...  # or sk_live_... for production
STRIPE_PUBLISHABLE_KEY=pk_test_...  # or pk_live_... for production
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_CONNECT_CLIENT_ID=ca_...  # For Connect OAuth (optional)
```

**Files to Update**:
1. Replace `services/agentic_stripe_client.py` → `services/stripe_client.py`
2. Update `services/smart_contract_wallet_manager.py` to use real Stripe client
3. Update `config/settings.py` to use `STRIPE_SECRET_KEY` instead of `agentic_stripe_api_key`
4. Update `api/webhooks.py` to handle real Stripe webhooks
5. Add `stripe==7.0.0` to `requirements.txt`

**Stripe Connect Setup Steps**:
1. Create Stripe account at https://dashboard.stripe.com/
2. Enable Stripe Connect in dashboard
3. Get API keys (Test mode for development)
4. Set up webhook endpoint: `https://your-domain.com/api/webhooks/stripe`
5. Configure Connect settings (Express accounts recommended)
6. Test with Stripe test cards: https://stripe.com/docs/testing

**Cost Structure**:
- **Standard Fees**: 2.9% + $0.30 per transaction
- **Connect Platform Fee**: 0.25% (optional, you can charge this)
- **No Monthly Fees**: Pay only per transaction
- **International**: Additional 1% for international cards

**Testing**:
- Use Stripe test mode: `sk_test_...` keys
- Test cards: https://stripe.com/docs/testing
- Test webhooks: Use Stripe CLI or dashboard

---

## 3. Coinbase Integration (Low Priority)

**Current Status**: Not implemented  
**File**: `services/coinbase_client.py` - Does not exist

### Required APIs:

**Coinbase Commerce API** (Recommended for Escrow)
- **Website**: https://commerce.coinbase.com/
- **API Documentation**: https://docs.cdp.coinbase.com/commerce/docs/
- **What You Need**:
  - Coinbase Commerce account
  - API Key
  - Webhook secret
- **Endpoints Needed**:
  - `POST /charges` - Create payment charge
  - `GET /charges/{id}` - Get charge status
  - `POST /checkouts` - Create checkout session
  - Webhook: Payment status updates
- **Cost**: 1% transaction fee
- **Integration Code Location**: `services/coinbase_client.py` (NEW FILE NEEDED)

**Alternative: Coinbase Advanced Trade API**
- **Website**: https://www.coinbase.com/advanced-trade
- **Use Case**: For more advanced crypto trading features
- **Cost**: 0.4-0.6% trading fees

**Alternative: Coinbase Wallet API**
- **Website**: https://www.coinbase.com/wallet
- **Use Case**: For wallet management
- **Cost**: Free (transaction fees apply)

#### Implementation Requirements:

```python
# services/coinbase_client.py (NEW FILE NEEDED)
class CoinbaseClient:
    def __init__(self, api_key: str, api_secret: str):
        """Initialize Coinbase client."""
    
    async def create_wallet(
        self,
        transaction_id: str,
        currency: str = "USD"
    ) -> Dict[str, Any]:  # Returns wallet_id, address
    
    async def create_payment_charge(
        self,
        amount: Decimal,
        currency: str,
        description: str
    ) -> Dict[str, Any]:  # Returns charge_id, payment_url
    
    async def get_charge_status(
        self,
        charge_id: str
    ) -> Dict[str, Any]:  # Returns status, transaction_hash
    
    async def execute_payment(
        self,
        wallet_id: str,
        recipient_address: str,
        amount: Decimal,
        currency: str
    ) -> Dict[str, Any]:  # Returns transaction_hash
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> bool:
```

**Environment Variables Needed**:
```bash
COINBASE_API_KEY=your_api_key
COINBASE_API_SECRET=your_api_secret
COINBASE_WEBHOOK_SECRET=your_webhook_secret
COINBASE_NETWORK=mainnet  # or testnet
```

**Integration Points**:
- Update `services/smart_contract_wallet_manager.py` to support Coinbase
- Add payment method selection (Stripe vs Coinbase)
- Update `models/payment.py` to track payment method

---

## 3. VAPI Voice Commands (Low Priority)

**Current Status**: API endpoints exist, but not in VAPI tool definitions  
**File**: `vapi_tools_config.json` - Only has 4 tools (search, analyze-risk, schedule, draft-offer)

### Required: Add Escrow Tools to VAPI

**Current VAPI Tools** (4):
1. `search_properties` ✅
2. `analyze_risk` ✅
3. `schedule_viewing` ✅
4. `draft_offer` ✅

**Missing Escrow Tools** (5+):

#### Tool 1: Check Escrow Status

**VAPI Tool Definition Needed**:
```json
{
  "type": "function",
  "function": {
    "name": "check_escrow_status",
    "description": "Check the status of an escrow transaction. Use this when the user asks about their escrow, transaction status, or what's happening with their purchase.",
    "parameters": {
      "type": "object",
      "properties": {
        "transaction_id": {
          "type": "string",
          "description": "Escrow transaction ID (optional, can be retrieved from user context)"
        },
        "user_id": {
          "type": "string",
          "description": "User identifier from conversation context"
        }
      },
      "required": ["user_id"]
    }
  },
  "server": {
    "url": "https://your-deployment-url.vercel.app/api/escrow/transactions/{transaction_id}/status",
    "method": "GET"
  }
}
```

**Backend Endpoint**: `GET /api/escrow/transactions/{transaction_id}/status` ✅ (Already exists)

---

#### Tool 2: Deposit Earnest Money

**VAPI Tool Definition Needed**:
```json
{
  "type": "function",
  "function": {
    "name": "deposit_earnest_money",
    "description": "Initiate earnest money deposit for an escrow transaction. Use this when the user wants to deposit earnest money or start the escrow process.",
    "parameters": {
      "type": "object",
      "properties": {
        "transaction_id": {
          "type": "string",
          "description": "Escrow transaction ID"
        },
        "amount": {
          "type": "number",
          "description": "Earnest money amount in dollars"
        },
        "payment_method": {
          "type": "string",
          "enum": ["stripe", "coinbase"],
          "description": "Payment method to use"
        },
        "user_id": {
          "type": "string",
          "description": "User identifier"
        }
      },
      "required": ["transaction_id", "amount", "user_id"]
    }
  },
  "server": {
    "url": "https://your-deployment-url.vercel.app/api/escrow/transactions/{transaction_id}/deposit",
    "method": "POST"
  }
}
```

**Backend Endpoint**: `POST /api/escrow/transactions/{transaction_id}/deposit` ✅ (Already exists)

---

#### Tool 3: Get Milestone Status

**VAPI Tool Definition Needed**:
```json
{
  "type": "function",
  "function": {
    "name": "get_milestone_status",
    "description": "Get the status of verification milestones (title search, inspection, appraisal, lending). Use this when the user asks about next steps, what's pending, or milestone progress.",
    "parameters": {
      "type": "object",
      "properties": {
        "transaction_id": {
          "type": "string",
          "description": "Escrow transaction ID"
        },
        "user_id": {
          "type": "string",
          "description": "User identifier"
        }
      },
      "required": ["transaction_id", "user_id"]
    }
  },
  "server": {
    "url": "https://your-deployment-url.vercel.app/api/escrow/transactions/{transaction_id}/milestones",
    "method": "GET"
  }
}
```

**Backend Endpoint**: `GET /api/escrow/transactions/{transaction_id}/milestones` ✅ (Check if exists)

---

#### Tool 4: Get Payment History

**VAPI Tool Definition Needed**:
```json
{
  "type": "function",
  "function": {
    "name": "get_payment_history",
    "description": "Get payment history for an escrow transaction. Use this when the user asks about payments made, who was paid, or payment status.",
    "parameters": {
      "type": "object",
      "properties": {
        "transaction_id": {
          "type": "string",
          "description": "Escrow transaction ID"
        },
        "user_id": {
          "type": "string",
          "description": "User identifier"
        }
      },
      "required": ["transaction_id", "user_id"]
    }
  },
  "server": {
    "url": "https://your-deployment-url.vercel.app/api/escrow/transactions/{transaction_id}/payments",
    "method": "GET"
  }
}
```

**Backend Endpoint**: `GET /api/escrow/transactions/{transaction_id}/payments` ✅ (Already exists in `api/escrow/payments.py`)

---

#### Tool 5: Create Escrow Transaction (Auto-triggered)

**Note**: This should be automatically triggered when an offer is accepted, but can also be manual.

**VAPI Tool Definition Needed**:
```json
{
  "type": "function",
  "function": {
    "name": "create_escrow_transaction",
    "description": "Create a new escrow transaction after an offer is accepted. This is typically automatic but can be manually triggered.",
    "parameters": {
      "type": "object",
      "properties": {
        "offer_id": {
          "type": "string",
          "description": "Offer ID from draft_offer"
        },
        "property_address": {
          "type": "string",
          "description": "Property address"
        },
        "purchase_price": {
          "type": "number",
          "description": "Purchase price in dollars"
        },
        "earnest_money": {
          "type": "number",
          "description": "Earnest money amount in dollars"
        },
        "user_id": {
          "type": "string",
          "description": "User identifier"
        }
      },
      "required": ["offer_id", "property_address", "purchase_price", "earnest_money", "user_id"]
    }
  },
  "server": {
    "url": "https://your-deployment-url.vercel.app/api/escrow/transactions",
    "method": "POST"
  }
}
```

**Backend Endpoint**: `POST /api/escrow/transactions` ✅ (Already exists)

---

## Summary of Required APIs

### Critical Priority (Blocks Production)

1. **Stripe API Integration** ⚠️ **CRITICAL**
   - **Status**: NOT IMPLEMENTED (placeholder code only)
   - **Required**: Stripe Connect API, Payment Intents, Transfers, Payouts
   - **Cost**: 2.9% + $0.30 per transaction
   - **Files to Replace**: `services/agentic_stripe_client.py` → `services/stripe_client.py`
   - **Action**: Implement real Stripe integration immediately

### High Priority (For Production)

2. **Title Company API**
   - **Recommended**: First American Title API
   - **Cost**: $50-200 per search
   - **Files to Create**: `services/title_company_client.py`
   - **Files to Update**: `agents/title_search_agent.py`

3. **Inspection Service API**
   - **Recommended**: HomeAdvisor API or custom inspector network
   - **Cost**: $50-150 per inspection
   - **Files to Create**: `services/inspection_client.py`
   - **Files to Update**: `agents/inspection_agent.py`

4. **Appraisal Service API**
   - **Recommended**: AMC API (AppraisalPort, AppraisalScope)
   - **Cost**: $300-600 per appraisal
   - **Files to Create**: `services/appraisal_client.py`
   - **Files to Update**: `agents/appraisal_agent.py`

5. **Lender API**
   - **Recommended**: Lender-specific API (Rocket Mortgage, Chase, etc.)
   - **Cost**: Free (part of loan process)
   - **Files to Create**: `services/lending_client.py`
   - **Files to Update**: `agents/lending_agent.py`

### Medium Priority (Enhancement)

6. **Coinbase API**
   - **Recommended**: Coinbase Commerce API
   - **Cost**: 1% transaction fee
   - **Files to Create**: `services/coinbase_client.py`
   - **Files to Update**: `services/smart_contract_wallet_manager.py`

### Low Priority (User Experience)

7. **VAPI Tool Definitions**
   - **Action**: Update `vapi_tools_config.json`
   - **Cost**: Free (just configuration)
   - **Files to Update**: `vapi_tools_config.json`, `scripts/update_vapi_config.py`

---

## Implementation Checklist

### Stripe Integration (CRITICAL - Do First)
- [ ] Create Stripe account at https://dashboard.stripe.com/
- [ ] Get API keys (test mode: `sk_test_...`)
- [ ] Enable Stripe Connect in dashboard
- [ ] Install Stripe Python SDK: `pip install stripe==7.0.0`
- [ ] Replace `services/agentic_stripe_client.py` with real Stripe implementation
- [ ] Update `services/smart_contract_wallet_manager.py` to use real Stripe client
- [ ] Update `config/settings.py` with `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET`
- [ ] Update `api/webhooks.py` to handle real Stripe webhooks
- [ ] Add Stripe webhook endpoint: `/api/webhooks/stripe`
- [ ] Test with Stripe test cards
- [ ] Update documentation

### Title Search Integration
- [ ] Choose title company API provider
- [ ] Get API credentials
- [ ] Create `services/title_company_client.py`
- [ ] Update `agents/title_search_agent.py:_perform_title_search()`
- [ ] Add `TITLE_COMPANY_API_KEY` to `.env`
- [ ] Test title search flow
- [ ] Update documentation

### Inspection Integration
- [ ] Choose inspection service API provider
- [ ] Get API credentials
- [ ] Create `services/inspection_client.py`
- [ ] Update `agents/inspection_agent.py:_perform_inspection()`
- [ ] Add `INSPECTION_SERVICE_API_KEY` to `.env`
- [ ] Test inspection booking flow
- [ ] Update documentation

### Appraisal Integration
- [ ] Choose appraisal service API provider
- [ ] Get API credentials
- [ ] Create `services/appraisal_client.py`
- [ ] Update `agents/appraisal_agent.py:_perform_appraisal()`
- [ ] Add `APPRAISAL_SERVICE_API_KEY` to `.env`
- [ ] Test appraisal ordering flow
- [ ] Update documentation

### Lending Integration
- [ ] Choose lender API provider
- [ ] Get API credentials (may require partnership)
- [ ] Create `services/lending_client.py`
- [ ] Update `agents/lending_agent.py:_verify_loan_status()`
- [ ] Add `LENDER_API_KEY` to `.env`
- [ ] Test loan verification flow
- [ ] Update documentation

### Coinbase Integration
- [ ] Create Coinbase Commerce account
- [ ] Get API credentials
- [ ] Create `services/coinbase_client.py`
- [ ] Update `services/smart_contract_wallet_manager.py` to support Coinbase
- [ ] Add Coinbase environment variables to `.env`
- [ ] Test crypto payment flow
- [ ] Update documentation

### VAPI Voice Commands
- [ ] Add 5 escrow tools to `vapi_tools_config.json`
- [ ] Update `scripts/update_vapi_config.py` to include escrow tools
- [ ] Test voice commands in VAPI dashboard
- [ ] Update VAPI documentation

---

## Estimated Costs

### Per Transaction Costs:
- Title Search: $50-200
- Inspection: $50-150
- Appraisal: $300-600
- Lending Verification: $0 (part of loan)
- **Total per transaction**: $400-950

### Monthly/Setup Costs:
- Title Company API: $0-500/month (depending on volume)
- Inspection Service: Commission-based or $0-300/month
- Appraisal Service: $0-500/month (depending on volume)
- Lender API: Free (partnership required)
- Coinbase: 1% transaction fee
- **Total monthly**: $0-1,300/month (volume-dependent)

---

## Quick Start Recommendations

### For MVP/Demo:
1. **Title**: Use TitleAPI.com (easier integration)
2. **Inspection**: Build simple inspector marketplace (manual booking)
3. **Appraisal**: Use RentCast AVM initially (upgrade later)
4. **Lending**: Manual verification initially (add API later)
5. **Coinbase**: Skip for MVP (Stripe only)
6. **VAPI**: Add escrow status commands

### For Production:
1. **Title**: First American Title API
2. **Inspection**: HomeAdvisor API or custom network
3. **Appraisal**: AMC API (AppraisalPort)
4. **Lending**: Lender-specific API (Rocket Mortgage)
5. **Coinbase**: Coinbase Commerce API
6. **VAPI**: All 5 escrow tools

---

**Document Version**: 1.0  
**Last Updated**: November 2024

