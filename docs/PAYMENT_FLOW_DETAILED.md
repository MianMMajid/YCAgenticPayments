# Detailed Payment Flow - Agent Credentials

**Status**: ✅ **Each agent uses its own credentials**

---

## Complete Payment Flow

### Example: Title Search Agent Payment

#### Step 1: Agent Initiates Payment

```python
# In agents/title_search_agent.py
agent_id = "title-agent"  # Internal identifier
recipient = settings.service_recipient_landamerica  # 0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d
amount_usdc = 0.03  # USDC
```

#### Step 2: x402 Protocol Handler

```python
# In services/x402_protocol_handler.py
result = await x402_handler.execute_x402_flow(
    service_url=service_url,
    amount=amount_usdc,
    agent_id="title-agent",  # Internal ID
    recipient="0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d"  # LandAmerica wallet
)
```

#### Step 3: Payment Handler Gets Agent-Specific Credentials

```python
# In services/locus_payment_handler.py
agent_type = "title"  # Extracted from "title-agent"

# Get actual Locus agent ID
actual_agent_id = self.locus.get_agent_id("title")
# Returns: "ooeju0aot520uv7dd77nr7d5r"

# Get agent-specific API key
agent_api_key = os.getenv("LOCUS_AGENT_TITLE_KEY")
# Returns: "locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG"
```

#### Step 4: Create API Client with Agent's Key

```python
# Create client with Title Agent's API key
api_client = LocusAPIClient(api_key="locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG")
```

#### Step 5: Execute Payment with Agent's Credentials

```python
payment_result = await api_client.execute_payment(
    agent_id="ooeju0aot520uv7dd77nr7d5r",  # Title Agent's actual ID
    amount=0.03,
    recipient_wallet="0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d",  # LandAmerica wallet
    currency="USDC",
    description="Title search payment"
)
```

#### Step 6: API Request

```http
POST https://api.paywithlocus.com/api/mcp/send_to_address
Authorization: Bearer locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG
Content-Type: application/json

{
  "address": "0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d",
  "amount": 0.03,
  "memo": "Title search payment"
}
```

---

## Agent Credential Mapping

| Agent Type | Internal ID | Locus Agent ID | API Key | Recipient Wallet |
|------------|-------------|----------------|---------|------------------|
| **Title** | `title-agent` | `ooeju0aot520uv7dd77nr7d5r` | `locus_dev_exC56yN_...` | `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d` |
| **Inspection** | `inspection-agent` | `2ss8gjcf4q8g05hueor4ftnuu7` | `locus_dev_NeMbZAgJFw...` | `0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9` |
| **Appraisal** | `appraisal-agent` | `7qictfjj57f973mfp0i4ku209k` | `locus_dev_y7wmTdasNB...` | `0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574` |
| **Underwriting** | `underwriting-agent` | `27fqhc1mtsd97q63bddaqoutmv` | `locus_dev_cRKUMxRuSS...` | `0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba` |

---

## Code Flow Summary

```
Agent (title_search_agent.py)
    ↓
    Uses: agent_id="title-agent", recipient=LandAmerica wallet
    ↓
x402 Protocol Handler
    ↓
    Passes: agent_id, recipient, amount
    ↓
Payment Handler (locus_payment_handler.py)
    ↓
    Extracts: agent_type="title"
    Gets: actual_agent_id="ooeju0aot520uv7dd77nr7d5r"
    Gets: agent_api_key="locus_dev_exC56yN_..."
    ↓
Locus API Client
    ↓
    Uses: Title Agent's API key for authentication
    Uses: Title Agent's ID in request
    ↓
Locus Backend API
    ↓
    Validates: Title Agent's credentials
    Executes: Payment from main wallet to LandAmerica wallet
    ↓
Locus Live Dashboard
    ↓
    Shows: Payment from Title Agent (ooeju0aot520uv7dd77nr7d5r)
```

---

## Key Points

1. **Each agent has unique credentials**:
   - Unique Agent ID
   - Unique API Key
   - Unique recipient wallet

2. **Payment handler automatically uses correct credentials**:
   - Maps internal agent ID to Locus agent ID
   - Gets agent-specific API key
   - Uses agent's recipient wallet

3. **Main wallet is the payment source**:
   - All payments come from Yc-MakeEmPay wallet
   - Each agent authenticates with its own credentials
   - Payments go to each agent's service wallet

4. **Locus Live tracking**:
   - Each payment shows which agent made it
   - Uses agent's actual Locus Agent ID
   - Tracks per-agent budget usage

---

## Verification

✅ **Title Agent**: Uses its own ID + API key + wallet  
✅ **Inspection Agent**: Uses its own ID + API key + wallet  
✅ **Appraisal Agent**: Uses its own ID + API key + wallet  
✅ **Underwriting Agent**: Uses its own ID + API key + wallet  
✅ **Main Wallet**: Source of all payments  

**Everything is correctly configured!**

---

**Status**: ✅ **READY** - Each agent uses its own credentials for A2A payments!

