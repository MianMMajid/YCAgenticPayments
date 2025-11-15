# Wallet Addresses Configuration Summary

**Date**: November 15, 2025  
**Status**: ✅ **COMPLETED**

---

## Wallet Addresses Configured

### Main Wallet (Payment Source)
- **Name**: Yc-MakeEmPay
- **Address**: `0x45B876546953Fe28C66022b48310dFbc1c2Fec47`
- **Private Key**: `0xfd7875c20892f146272f8733a5d037d24da4ceffe8b59d90dc30709aea2bb0e1`
- **Chain ID**: 8453 (Base Mainnet)
- **Purpose**: Main wallet that sends payments to service providers
- **Balance**: $10.00 USDC

### Service Recipient Wallets (Payment Destinations)

#### 1. LandAmerica Title Search
- **Name**: LandAmerica Wallet
- **Address**: `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d`
- **Private Key**: `0x3175ee459952384c38d445f4df941096eb04f8e9b49292bec1aa0dbb46d8583a`
- **Service**: Title Search and Verification
- **Payment Amount**: $1,200.00 USD → 1.2 USDC

#### 2. AmeriSpec Inspection
- **Name**: AmeriSpec Wallet
- **Address**: `0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9`
- **Private Key**: `0x29e9f4f25c2c1303f96526900488e66834e98369744465e3215029b281de8661`
- **Service**: Property Inspection
- **Payment Amount**: $500.00 USD → 0.5 USDC

#### 3. CoreLogic Valuation
- **Name**: CoreLogic Wallet
- **Address**: `0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574`
- **Private Key**: `0xd832e2e266dbcf0a05373ee4d30a0ce2b1f1b15cb5bbb7f85a35b8ecc49c81af`
- **Service**: Property Appraisal and Valuation
- **Payment Amount**: $400.00 USD → 0.4 USDC

#### 4. Fannie Mae Verification
- **Name**: Fannie Mae Wallet
- **Address**: `0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba`
- **Private Key**: `0xa94e4fe9b8535a5ca4e19d9a99163f41f4c24e508c349d4db264cf11780599f8`
- **Service**: Loan Verification
- **Payment Amount**: $0.00 USD → 0.0 USDC (signature required, no payment)

---

## Environment Variables Added

The following variables have been added to `.env`:

```bash
# Service Recipient Wallet Addresses
SERVICE_RECIPIENT_LANDAMERICA=0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d
SERVICE_RECIPIENT_AMERISPEC=0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9
SERVICE_RECIPIENT_CORELOGIC=0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574
SERVICE_RECIPIENT_FANNIEMAE=0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba
```

---

## Settings Configuration

Added to `config/settings.py`:

```python
# Service Recipient Wallet Addresses (where payments are sent)
service_recipient_landamerica: str = "0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d"
service_recipient_amerispec: str = "0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9"
service_recipient_corelogic: str = "0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574"
service_recipient_fanniemae: str = "0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba"
```

---

## Agent Updates

All 4 agents have been updated to use settings instead of hardcoded addresses:

### ✅ Title Search Agent
- **File**: `agents/title_search_agent.py`
- **Change**: Uses `settings.service_recipient_landamerica`
- **Before**: Hardcoded `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d`
- **After**: `settings.service_recipient_landamerica`

### ✅ Inspection Agent
- **File**: `agents/inspection_agent.py`
- **Change**: Uses `settings.service_recipient_amerispec`
- **Before**: Hardcoded `0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9`
- **After**: `settings.service_recipient_amerispec`

### ✅ Appraisal Agent
- **File**: `agents/appraisal_agent.py`
- **Change**: Uses `settings.service_recipient_corelogic`
- **Before**: Hardcoded `0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574`
- **After**: `settings.service_recipient_corelogic`

### ✅ Lending Agent
- **File**: `agents/lending_agent.py`
- **Change**: Uses `settings.service_recipient_fanniemae`
- **Before**: Hardcoded `0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba`
- **After**: `settings.service_recipient_fanniemae`

---

## Payment Flow

```
Main Wallet (Yc-MakeEmPay)
    ↓
    ├─→ LandAmerica Wallet ($1,200 → 1.2 USDC)
    ├─→ AmeriSpec Wallet ($500 → 0.5 USDC)
    ├─→ CoreLogic Wallet ($400 → 0.4 USDC)
    └─→ Fannie Mae Wallet ($0 → 0.0 USDC, signature only)
```

---

## Verification

All wallet addresses have been verified and are properly configured:

✅ Main Wallet: `0x45B876546953Fe28C66022b48310dFbc1c2Fec47`  
✅ LandAmerica Recipient: `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d`  
✅ AmeriSpec Recipient: `0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9`  
✅ CoreLogic Recipient: `0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574`  
✅ Fannie Mae Recipient: `0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba`

---

## Benefits

1. **Centralized Configuration**: All wallet addresses in one place (`.env` and `settings.py`)
2. **Easy Updates**: Change addresses without modifying agent code
3. **Environment-Specific**: Different addresses for dev/staging/prod
4. **Type Safety**: Settings class provides type hints and validation
5. **Documentation**: Clear naming convention for each service

---

## Security Notes

- ✅ Wallet addresses are public (safe to store in `.env`)
- ⚠️ **Private keys should NEVER be committed to git**
- ⚠️ Private keys are stored in separate wallet JSON files (not in `.env`)
- ⚠️ Only the main wallet's private key is needed in `.env` (for signing payments)
- ⚠️ Service recipient private keys are not needed (they only receive payments)

---

## Next Steps

1. ✅ **Completed**: All wallet addresses added to `.env`
2. ✅ **Completed**: Settings updated with recipient addresses
3. ✅ **Completed**: All agents updated to use settings
4. ⏳ **Pending**: Get Policy Group IDs from Locus Dashboard
5. ⏳ **Pending**: Test full payment flow with real Locus API

---

**Configuration Completed**: November 15, 2025  
**Script Used**: `scripts/update_agent_credentials.py`

