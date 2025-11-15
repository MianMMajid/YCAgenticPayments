# Simplified Locus Architecture

**Date**: November 15, 2025  
**Status**: ✅ **ARCHITECTURE CLARIFIED**

---

## Architecture Overview

The Locus integration uses a **simple architecture** with:
- **Agent IDs** - For authentication
- **Individual Wallets** - For sending and receiving payments
- **No Policy Groups** - Not needed in this setup

---

## Components

### 1. Main Wallet (Payment Source)
- **Wallet**: Yc-MakeEmPay
- **Address**: `0x45B876546953Fe28C66022b48310dFbc1c2Fec47`
- **Purpose**: Sends payments to service providers
- **Balance**: $10.00 USDC

### 2. Agent IDs & API Keys
Each agent has:
- **Agent ID**: Unique identifier for the agent
- **API Key**: For authentication with Locus

| Agent | Agent ID | API Key |
|-------|----------|---------|
| Title Search | `ooeju0aot520uv7dd77nr7d5r` | `locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG` |
| Inspection | `2ss8gjcf4q8g05hueor4ftnuu7` | `locus_dev_NeMbZAgJFwpWXIrGaiZQTWm-Fhnpsxfd` |
| Appraisal | `7qictfjj57f973mfp0i4ku209k` | `locus_dev_y7wmTdasNBO4gCsFxWJnQ8bo0IROSOKk` |
| Underwriting | `27fqhc1mtsd97q63bddaqoutmv` | `locus_dev_cRKUMxRuSSjqaQzRgdbdhm5Jz2-szqVl` |

### 3. Service Recipient Wallets
Each service provider has their own wallet to receive payments:

| Service | Wallet Address | Purpose |
|---------|---------------|---------|
| LandAmerica | `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d` | Receives title search payments |
| AmeriSpec | `0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9` | Receives inspection payments |
| CoreLogic | `0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574` | Receives appraisal payments |
| Fannie Mae | `0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba` | Receives loan verification payments |

---

## Payment Flow

```
Main Wallet (Yc-MakeEmPay)
    ↓
Agent authenticates with Agent ID + API Key
    ↓
Agent requests payment to service wallet
    ↓
Locus processes payment
    ↓
Payment sent to service wallet
```

### Example: Title Search Payment

1. **Title Search Agent** authenticates:
   - Agent ID: `ooeju0aot520uv7dd77nr7d5r`
   - API Key: `locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG`

2. **Agent requests payment**:
   - From: Main Wallet (`0x45B876546953Fe28C66022b48310dFbc1c2Fec47`)
   - To: LandAmerica Wallet (`0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d`)
   - Amount: $0.03 USDC

3. **Locus processes**:
   - Validates agent credentials
   - Checks budget
   - Executes payment

4. **Payment completed**:
   - Transaction hash returned
   - Service receives payment

---

## Environment Variables

### Required Configuration

```bash
# Main Wallet
LOCUS_WALLET_ADDRESS=0x45B876546953Fe28C66022b48310dFbc1c2Fec47
LOCUS_WALLET_PRIVATE_KEY=0xfd7875c20892f146272f8733a5d037d24da4ceffe8b59d90dc30709aea2bb0e1
LOCUS_CHAIN_ID=8453
LOCUS_WALLET_NAME=Yc-MakeEmPay

# Locus API Key (can use any agent's API key)
LOCUS_API_KEY=locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG

# Agent IDs & Keys
LOCUS_AGENT_TITLE_ID=ooeju0aot520uv7dd77nr7d5r
LOCUS_AGENT_TITLE_KEY=locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG

LOCUS_AGENT_INSPECTION_ID=2ss8gjcf4q8g05hueor4ftnuu7
LOCUS_AGENT_INSPECTION_KEY=locus_dev_NeMbZAgJFwpWXIrGaiZQTWm-Fhnpsxfd

LOCUS_AGENT_APPRAISAL_ID=7qictfjj57f973mfp0i4ku209k
LOCUS_AGENT_APPRAISAL_KEY=locus_dev_y7wmTdasNBO4gCsFxWJnQ8bo0IROSOKk

LOCUS_AGENT_UNDERWRITING_ID=27fqhc1mtsd97q63bddaqoutmv
LOCUS_AGENT_UNDERWRITING_KEY=locus_dev_cRKUMxRuSSjqaQzRgdbdhm5Jz2-szqVl

# Service Recipient Wallets
SERVICE_RECIPIENT_LANDAMERICA=0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d
SERVICE_RECIPIENT_AMERISPEC=0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9
SERVICE_RECIPIENT_CORELOGIC=0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574
SERVICE_RECIPIENT_FANNIEMAE=0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba

# Agent Budgets (in USDC)
AGENT_TITLE_BUDGET=0.03
AGENT_INSPECTION_BUDGET=0.012
AGENT_APPRAISAL_BUDGET=0.010
AGENT_UNDERWRITING_BUDGET=0.019
```

### Not Needed
- ❌ Policy Group IDs (not used)
- ❌ Policy Group configuration (not needed)

---

## Code Structure

### Services

1. **`locus_wallet_manager.py`**
   - Manages main wallet
   - Validates wallet credentials
   - Provides wallet info

2. **`locus_integration.py`**
   - Manages agent IDs and budgets
   - No Policy Group references
   - Budget tracking per agent

3. **`locus_payment_handler.py`**
   - Processes payments using Agent IDs
   - Validates budgets
   - Creates payment records

4. **`x402_protocol_handler.py`**
   - Handles x402 payment protocol
   - Integrates with payment handler
   - Manages payment flow

### Agents

Each agent:
- Uses its Agent ID for authentication
- Sends payments to service wallet
- No Policy Group needed

---

## Key Differences from Previous Understanding

### Before (Incorrect)
- ❌ Policy Groups required
- ❌ Policy Group IDs needed
- ❌ Complex Policy → Agent → Wallet mapping

### Now (Correct)
- ✅ Only Agent IDs needed
- ✅ Direct Agent → Wallet payment flow
- ✅ Simple architecture

---

## Verification Checklist

- [x] Main wallet configured
- [x] All 4 Agent IDs configured
- [x] All 4 Agent API Keys configured
- [x] All 4 Service recipient wallets configured
- [x] Budgets configured
- [x] Code updated to remove Policy Group references
- [ ] Test with real Locus API

---

## Status

✅ **ARCHITECTURE SIMPLIFIED** - No Policy Groups needed, just Agent IDs and wallets!

**Ready for**: Full Locus integration testing

