# Complete Agent Credentials Configuration

**Status**: ✅ **ALL AGENTS FULLY CONFIGURED**

---

## Main Account (Payment Source)

- **Wallet Name**: Yc-MakeEmPay
- **Wallet Address**: `0x45B876546953Fe28C66022b48310dFbc1c2Fec47`
- **Private Key**: `0xfd7875c20892f146272f8733a5d037d24da4ceffe8b59d90dc30709aea2bb0e1`
- **Chain ID**: 8453 (Base Mainnet)
- **Balance**: $10.00 USDC
- **Purpose**: Sends payments to service providers

---

## Agent Configurations

### 1. Title Search Agent

**Agent Credentials**:
- **Agent ID**: `ooeju0aot520uv7dd77nr7d5r`
- **API Key**: `locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG`

**Recipient Wallet**:
- **Address**: `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d`
- **Name**: LandAmerica Wallet
- **Service**: Title Search and Verification
- **Payment Amount**: $1,200.00 USD → 1.2 USDC

**Usage**:
- Agent authenticates with its own API key
- Makes payment from main wallet to LandAmerica wallet
- Payment appears in Locus Live dashboard

---

### 2. Inspection Agent

**Agent Credentials**:
- **Agent ID**: `2ss8gjcf4q8g05hueor4ftnuu7`
- **API Key**: `locus_dev_NeMbZAgJFwpWXIrGaiZQTWm-Fhnpsxfd`

**Recipient Wallet**:
- **Address**: `0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9`
- **Name**: AmeriSpec Wallet
- **Service**: Property Inspection
- **Payment Amount**: $500.00 USD → 0.5 USDC

**Usage**:
- Agent authenticates with its own API key
- Makes payment from main wallet to AmeriSpec wallet
- Payment appears in Locus Live dashboard

---

### 3. Appraisal Agent

**Agent Credentials**:
- **Agent ID**: `7qictfjj57f973mfp0i4ku209k`
- **API Key**: `locus_dev_y7wmTdasNBO4gCsFxWJnQ8bo0IROSOKk`

**Recipient Wallet**:
- **Address**: `0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574`
- **Name**: CoreLogic Wallet
- **Service**: Property Appraisal and Valuation
- **Payment Amount**: $400.00 USD → 0.4 USDC

**Usage**:
- Agent authenticates with its own API key
- Makes payment from main wallet to CoreLogic wallet
- Payment appears in Locus Live dashboard

---

### 4. Underwriting Agent

**Agent Credentials**:
- **Agent ID**: `27fqhc1mtsd97q63bddaqoutmv`
- **API Key**: `locus_dev_cRKUMxRuSSjqaQzRgdbdhm5Jz2-szqVl`

**Recipient Wallet**:
- **Address**: `0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba`
- **Name**: Fannie Mae Wallet
- **Service**: Loan Verification
- **Payment Amount**: $0.00 USD → 0.0 USDC (signature required, no payment)

**Usage**:
- Agent authenticates with its own API key
- Makes payment from main wallet to Fannie Mae wallet
- Payment appears in Locus Live dashboard

---

## Payment Flow

```
Main Wallet (Yc-MakeEmPay)
    ↓
    ├─→ Title Agent (uses own API key + agent ID)
    │   └─→ Payment to LandAmerica Wallet
    │
    ├─→ Inspection Agent (uses own API key + agent ID)
    │   └─→ Payment to AmeriSpec Wallet
    │
    ├─→ Appraisal Agent (uses own API key + agent ID)
    │   └─→ Payment to CoreLogic Wallet
    │
    └─→ Underwriting Agent (uses own API key + agent ID)
        └─→ Payment to Fannie Mae Wallet
```

---

## How It Works in Code

### Payment Handler Logic

1. **Agent calls payment handler**:
   ```python
   await payment_handler.execute_payment(
       agent_id="title-agent",  # Internal agent identifier
       amount=0.03,
       recipient="0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d",
       ...
   )
   ```

2. **Payment handler extracts agent type**:
   - `"title-agent"` → `"title"`

3. **Gets agent-specific credentials**:
   ```python
   actual_agent_id = "ooeju0aot520uv7dd77nr7d5r"  # From LOCUS_AGENT_TITLE_ID
   agent_api_key = "locus_dev_exC56yN_..."  # From LOCUS_AGENT_TITLE_KEY
   ```

4. **Creates API client with agent's key**:
   ```python
   api_client = LocusAPIClient(api_key=agent_api_key)
   ```

5. **Makes payment using agent's credentials**:
   ```python
   payment_result = await api_client.execute_payment(
       agent_id=actual_agent_id,  # Agent's actual ID
       amount=amount,
       recipient_wallet=recipient,  # Service wallet
       ...
   )
   ```

---

## Environment Variables

All configured in `.env`:

```bash
# Main Wallet
LOCUS_WALLET_ADDRESS=0x45B876546953Fe28C66022b48310dFbc1c2Fec47
LOCUS_WALLET_PRIVATE_KEY=0xfd7875c20892f146272f8733a5d037d24da4ceffe8b59d90dc30709aea2bb0e1
LOCUS_WALLET_NAME=Yc-MakeEmPay
LOCUS_CHAIN_ID=8453

# Title Agent
LOCUS_AGENT_TITLE_ID=ooeju0aot520uv7dd77nr7d5r
LOCUS_AGENT_TITLE_KEY=locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG
SERVICE_RECIPIENT_LANDAMERICA=0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d

# Inspection Agent
LOCUS_AGENT_INSPECTION_ID=2ss8gjcf4q8g05hueor4ftnuu7
LOCUS_AGENT_INSPECTION_KEY=locus_dev_NeMbZAgJFwpWXIrGaiZQTWm-Fhnpsxfd
SERVICE_RECIPIENT_AMERISPEC=0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9

# Appraisal Agent
LOCUS_AGENT_APPRAISAL_ID=7qictfjj57f973mfp0i4ku209k
LOCUS_AGENT_APPRAISAL_KEY=locus_dev_y7wmTdasNBO4gCsFxWJnQ8bo0IROSOKk
SERVICE_RECIPIENT_CORELOGIC=0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574

# Underwriting Agent
LOCUS_AGENT_UNDERWRITING_ID=27fqhc1mtsd97q63bddaqoutmv
LOCUS_AGENT_UNDERWRITING_KEY=locus_dev_cRKUMxRuSSjqaQzRgdbdhm5Jz2-szqVl
SERVICE_RECIPIENT_FANNIEMAE=0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba
```

---

## Verification

✅ **Main Wallet**: Configured  
✅ **Title Agent**: ID + API Key + Wallet  
✅ **Inspection Agent**: ID + API Key + Wallet  
✅ **Appraisal Agent**: ID + API Key + Wallet  
✅ **Underwriting Agent**: ID + API Key + Wallet  

**All agents are fully configured with their own credentials!**

---

## Making Payments

Each agent makes payments using:
1. **Its own Agent ID** - For identification in Locus
2. **Its own API Key** - For authentication
3. **Service recipient wallet** - Where payment goes
4. **Main wallet** - Source of funds (Yc-MakeEmPay)

This ensures:
- ✅ Each agent is properly authenticated
- ✅ Payments are tracked per agent
- ✅ Budgets are managed per agent
- ✅ Payments appear in Locus Live with correct agent attribution

---

**Status**: ✅ **COMPLETE** - All agents configured with individual credentials!

