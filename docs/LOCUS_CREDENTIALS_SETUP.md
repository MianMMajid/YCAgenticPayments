# Locus Credentials Setup Guide

## ✅ Wallet Information (Already Configured)

### Main Wallet (Yc-MakeEmPay)
- **Address**: `0x45B876546953Fe28C66022b48310dFbc1c2Fec47`
- **Private Key**: `0xfd7875c20892f146272f8733a5d037d24da4ceffe8b59d90dc30709aea2bb0e1`
- **Chain ID**: `8453` (Base Mainnet)
- **Name**: Yc-MakeEmPay

### Service Recipient Wallets

#### LandAmerica Wallet
- **Address**: `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d`
- **Private Key**: `0x3175ee459952384c38d445f4df941096eb04f8e9b49292bec1aa0dbb46d8583a`
- **Used for**: Title Search payments

#### AmeriSpec Wallet
- **Address**: `0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9`
- **Private Key**: `0x29e9f4f25c2c1303f96526900488e66834e98369744465e3215029b281de8661`
- **Used for**: Inspection payments

#### CoreLogic Wallet
- **Address**: `0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574`
- **Private Key**: `0xd832e2e266dbcf0a05373ee4d30a0ce2b1f1b15cb5bbb7f85a35b8ecc49c81af`
- **Used for**: Appraisal payments

#### Fannie Mae Wallet
- **Address**: `0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba`
- **Private Key**: `0xa94e4fe9b8535a5ca4e19d9a99163f41f4c24e508c349d4db264cf11780599f8`
- **Used for**: Underwriting/Loan verification payments

---

## ✅ Agent API Keys (Already Configured)

### Title Search Agent
- **API Key**: `locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG`
- **Policy**: LandAmerica Title Verification Policy
- **Budget**: $0.03/day
- **Status**: Active

### Inspection Agent
- **API Key**: `locus_dev_NeMbZAgJFwpWXIrGaiZQTWm-Fhnpsxfd`
- **Policy**: AmeriSpec Home Inspection Policy
- **Budget**: $0.012/day
- **Status**: Active

### Appraisal Agent
- **API Key**: `locus_dev_y7wmTdasNBO4gCsFxWJnQ8bo0IROSOKk`
- **Policy**: CoreLogic Property Valuation Policy
- **Budget**: $0.010/day
- **Status**: Active

### Underwriting Agent
- **API Key**: `locus_dev_cRKUMxRuSSjqaQzRgdbdhm5Jz2-szqVl`
- **Policy**: Fannie Mae Loan Verification Policy
- **Budget**: $0.019/day
- **Status**: Active

---

## ⚠️ Still Needed from Locus Dashboard

### Policy Group IDs (Connected to Company Wallets)

**Important**: Each Policy Group is connected to a specific company wallet. When retrieving Policy Group IDs, verify they match the correct wallet address.

You need to get these from your Locus Dashboard:

- `LOCUS_POLICY_TITLE_ID` 
  - **Policy Group**: "LandAmerica Title Verification Policy"
  - **Connected Wallet**: `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d`
  - **How to Find**: Navigate to Policy Groups → "LandAmerica Title Verification Policy" → Copy Policy Group ID

- `LOCUS_POLICY_INSPECTION_ID`
  - **Policy Group**: "AmeriSpec Home Inspection Policy"
  - **Connected Wallet**: `0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9`
  - **How to Find**: Navigate to Policy Groups → "AmeriSpec Home Inspection Policy" → Copy Policy Group ID

- `LOCUS_POLICY_APPRAISAL_ID`
  - **Policy Group**: "CoreLogic Property Valuation Policy"
  - **Connected Wallet**: `0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574`
  - **How to Find**: Navigate to Policy Groups → "CoreLogic Property Valuation Policy" → Copy Policy Group ID

- `LOCUS_POLICY_UNDERWRITING_ID`
  - **Policy Group**: "Fannie Mae Loan Verification Policy"
  - **Connected Wallet**: `0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba`
  - **How to Find**: Navigate to Policy Groups → "Fannie Mae Loan Verification Policy" → Copy Policy Group ID

**Alternative Method**: You can also find Policy Group IDs by:
1. Navigate to **Wallets** section
2. Click on the company wallet address
3. View associated **Policy Groups**
4. Copy the Policy Group ID

See `docs/POLICY_GROUP_WALLET_MAPPING.md` for complete mapping details.

### Agent IDs
You need to get these from your Locus Dashboard:
- `LOCUS_AGENT_TITLE_ID` - From "Title Search Agent"
- `LOCUS_AGENT_INSPECTION_ID` - From "Inspection Agent"
- `LOCUS_AGENT_APPRAISAL_ID` - From "Appraisal Agent"
- `LOCUS_AGENT_UNDERWRITING_ID` - From "Underwriting Agent"

---

## 📝 Complete .env Configuration

Add these to your `.env` file:

```bash
# Main Wallet
LOCUS_WALLET_ADDRESS=0x45B876546953Fe28C66022b48310dFbc1c2Fec47
LOCUS_WALLET_PRIVATE_KEY=0xfd7875c20892f146272f8733a5d037d24da4ceffe8b59d90dc30709aea2bb0e1
LOCUS_CHAIN_ID=8453
LOCUS_WALLET_NAME=Yc-MakeEmPay

# Locus API Key (use any agent key as main key)
LOCUS_API_KEY=locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG

# Policy IDs (GET FROM LOCUS DASHBOARD)
LOCUS_POLICY_TITLE_ID=policy_title_[from_locus]
LOCUS_POLICY_INSPECTION_ID=policy_inspection_[from_locus]
LOCUS_POLICY_APPRAISAL_ID=policy_appraisal_[from_locus]
LOCUS_POLICY_UNDERWRITING_ID=policy_underwriting_[from_locus]

# Agent IDs & Keys
LOCUS_AGENT_TITLE_ID=agent_title_[from_locus]
LOCUS_AGENT_TITLE_KEY=locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG

LOCUS_AGENT_INSPECTION_ID=agent_inspection_[from_locus]
LOCUS_AGENT_INSPECTION_KEY=locus_dev_NeMbZAgJFwpWXIrGaiZQTWm-Fhnpsxfd

LOCUS_AGENT_APPRAISAL_ID=agent_appraisal_[from_locus]
LOCUS_AGENT_APPRAISAL_KEY=locus_dev_y7wmTdasNBO4gCsFxWJnQ8bo0IROSOKk

LOCUS_AGENT_UNDERWRITING_ID=agent_underwriting_[from_locus]
LOCUS_AGENT_UNDERWRITING_KEY=locus_dev_cRKUMxRuSSjqaQzRgdbdhm5Jz2-szqVl

# Budgets
AGENT_TITLE_BUDGET=0.03
AGENT_INSPECTION_BUDGET=0.012
AGENT_APPRAISAL_BUDGET=0.010
AGENT_UNDERWRITING_BUDGET=0.019

# Mock Services
LANDAMERICA_SERVICE=http://localhost:5001/landamerica/title-search
AMERISPEC_SERVICE=http://localhost:5001/amerispec/inspection
CORELOGIC_SERVICE=http://localhost:5001/corelogic/valuation
FANNIEMAE_SERVICE=http://localhost:5001/fanniemae/verify

# Mode
DEMO_MODE=true
USE_MOCK_SERVICES=true
```

---

## ✅ What's Already Done

1. ✅ **Wallet addresses updated** in all 4 agents
2. ✅ **Recipient addresses** set to correct service wallets
3. ✅ **API keys** documented
4. ✅ **Code updated** to use correct addresses

---

## 🔍 How to Find Policy & Agent IDs

1. Log into Locus Dashboard
2. Navigate to **Policies** section
3. Click on each policy to see its ID (format: `policy_xxxxx`)
4. Navigate to **Agents** section
5. Click on each agent to see its ID (format: `agent_xxxxx`)

---

## 🚀 Next Steps

1. **Get Policy IDs** from Locus Dashboard
2. **Get Agent IDs** from Locus Dashboard
3. **Add all values** to `.env` file
4. **Set `USE_MOCK_SERVICES=false`** when ready for production
5. **Test** with real Locus payments

---

## 📋 Quick Reference

| Service | Recipient Wallet | API Key |
|---------|-----------------|---------|
| LandAmerica | `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d` | `locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG` |
| AmeriSpec | `0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9` | `locus_dev_NeMbZAgJFwpWXIrGaiZQTWm-Fhnpsxfd` |
| CoreLogic | `0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574` | `locus_dev_y7wmTdasNBO4gCsFxWJnQ8bo0IROSOKk` |
| Fannie Mae | `0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba` | `locus_dev_cRKUMxRuSSjqaQzRgdbdhm5Jz2-szqVl` |

---

**Status**: ✅ Wallets and API keys configured. Need Policy IDs and Agent IDs from Locus Dashboard.

