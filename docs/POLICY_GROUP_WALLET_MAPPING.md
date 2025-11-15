# Policy Group to Wallet Mapping

**Date**: November 15, 2025  
**Status**: ✅ **MAPPING DEFINED**

---

## Understanding the Relationship

Each **Policy Group** in Locus is connected to a specific **Company Wallet**. When you create a Policy Group in the Locus Dashboard, it's associated with the wallet address of that company.

---

## Wallet → Policy Group Mapping

### 1. LandAmerica Title Verification
- **Company Wallet**: `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d`
- **Policy Group Name**: "LandAmerica Title Verification Policy"
- **Policy Group ID**: `LOCUS_POLICY_TITLE_ID` (to be retrieved from dashboard)
- **Agent**: Title Search Agent
- **Agent ID**: `ooeju0aot520uv7dd77nr7d5r`
- **Budget**: $0.03/day

### 2. AmeriSpec Home Inspection
- **Company Wallet**: `0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9`
- **Policy Group Name**: "AmeriSpec Home Inspection Policy"
- **Policy Group ID**: `LOCUS_POLICY_INSPECTION_ID` (to be retrieved from dashboard)
- **Agent**: Inspection Agent
- **Agent ID**: `2ss8gjcf4q8g05hueor4ftnuu7`
- **Budget**: $0.012/day

### 3. CoreLogic Property Valuation
- **Company Wallet**: `0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574`
- **Policy Group Name**: "CoreLogic Property Valuation Policy"
- **Policy Group ID**: `LOCUS_POLICY_APPRAISAL_ID` (to be retrieved from dashboard)
- **Agent**: Appraisal Agent
- **Agent ID**: `7qictfjj57f973mfp0i4ku209k`
- **Budget**: $0.010/day

### 4. Fannie Mae Loan Verification
- **Company Wallet**: `0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba`
- **Policy Group Name**: "Fannie Mae Loan Verification Policy"
- **Policy Group ID**: `LOCUS_POLICY_UNDERWRITING_ID` (to be retrieved from dashboard)
- **Agent**: Underwriting Agent
- **Agent ID**: `27fqhc1mtsd97q63bddaqoutmv`
- **Budget**: $0.019/day

---

## How to Find Policy Group IDs in Locus Dashboard

Since Policy Groups are connected to company wallets, you can find them by:

### Method 1: Via Wallet
1. Log into [Locus Dashboard](https://app.paywithlocus.com)
2. Navigate to **Wallets** section
3. Find the company wallet (e.g., `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d`)
4. Click on the wallet
5. View associated **Policy Groups**
6. Copy the Policy Group ID (format: `policy_xxxxx`)

### Method 2: Via Policy Groups
1. Log into [Locus Dashboard](https://app.paywithlocus.com)
2. Navigate to **Policy Groups** section
3. Find the policy by name:
   - "LandAmerica Title Verification Policy"
   - "AmeriSpec Home Inspection Policy"
   - "CoreLogic Property Valuation Policy"
   - "Fannie Mae Loan Verification Policy"
4. Click on the policy
5. View the **Policy Group ID** (format: `policy_xxxxx`)
6. Verify it's associated with the correct wallet address

### Method 3: Via Agent
1. Log into [Locus Dashboard](https://app.paywithlocus.com)
2. Navigate to **Agents** section
3. Click on an agent (e.g., "Title Search Agent")
4. View the **Associated Policy Group**
5. Copy the Policy Group ID

---

## Complete Mapping Table

| Service | Wallet Address | Policy Group Name | Policy Group ID (ENV) | Agent ID | Agent API Key |
|---------|---------------|-------------------|----------------------|----------|---------------|
| **LandAmerica** | `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d` | LandAmerica Title Verification Policy | `LOCUS_POLICY_TITLE_ID` | `ooeju0aot520uv7dd77nr7d5r` | `locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG` |
| **AmeriSpec** | `0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9` | AmeriSpec Home Inspection Policy | `LOCUS_POLICY_INSPECTION_ID` | `2ss8gjcf4q8g05hueor4ftnuu7` | `locus_dev_NeMbZAgJFwpWXIrGaiZQTWm-Fhnpsxfd` |
| **CoreLogic** | `0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574` | CoreLogic Property Valuation Policy | `LOCUS_POLICY_APPRAISAL_ID` | `7qictfjj57f973mfp0i4ku209k` | `locus_dev_y7wmTdasNBO4gCsFxWJnQ8bo0IROSOKk` |
| **Fannie Mae** | `0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba` | Fannie Mae Loan Verification Policy | `LOCUS_POLICY_UNDERWRITING_ID` | `27fqhc1mtsd97q63bddaqoutmv` | `locus_dev_cRKUMxRuSSjqaQzRgdbdhm5Jz2-szqVl` |

---

## Payment Flow with Policy Groups

```
Main Wallet (Yc-MakeEmPay)
    ↓
    ├─→ Policy Group: LandAmerica Title Verification
    │   └─→ Wallet: 0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d
    │
    ├─→ Policy Group: AmeriSpec Home Inspection
    │   └─→ Wallet: 0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9
    │
    ├─→ Policy Group: CoreLogic Property Valuation
    │   └─→ Wallet: 0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574
    │
    └─→ Policy Group: Fannie Mae Loan Verification
        └─→ Wallet: 0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba
```

---

## Environment Variables Needed

Once you retrieve the Policy Group IDs from the Locus Dashboard, add them to `.env`:

```bash
# Policy Group IDs (connected to company wallets)
LOCUS_POLICY_TITLE_ID=policy_xxxxx          # From LandAmerica wallet/policy
LOCUS_POLICY_INSPECTION_ID=policy_xxxxx     # From AmeriSpec wallet/policy
LOCUS_POLICY_APPRAISAL_ID=policy_xxxxx      # From CoreLogic wallet/policy
LOCUS_POLICY_UNDERWRITING_ID=policy_xxxxx   # From Fannie Mae wallet/policy
```

---

## Verification Checklist

When you retrieve Policy Group IDs, verify:

- [ ] **LandAmerica Policy ID** matches wallet `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d`
- [ ] **AmeriSpec Policy ID** matches wallet `0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9`
- [ ] **CoreLogic Policy ID** matches wallet `0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574`
- [ ] **Fannie Mae Policy ID** matches wallet `0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba`
- [ ] Each Policy Group has the correct budget configured
- [ ] Each Agent is associated with the correct Policy Group

---

## Important Notes

1. **One-to-One Relationship**: Each company wallet has exactly one Policy Group
2. **Policy Group Controls**: The Policy Group defines:
   - Budget limits
   - Payment permissions
   - Approved contacts (wallet addresses)
3. **Agent Association**: Each agent is linked to a Policy Group
4. **Payment Authorization**: When an agent makes a payment, Locus checks:
   - Agent has access to the Policy Group
   - Policy Group has budget available
   - Recipient wallet is approved in Policy Group

---

## Next Steps

1. ✅ **Completed**: Wallet addresses configured
2. ✅ **Completed**: Agent IDs and API keys configured
3. ⏳ **Pending**: Retrieve Policy Group IDs from Locus Dashboard
4. ⏳ **Pending**: Add Policy Group IDs to `.env`
5. ⏳ **Pending**: Verify Policy Group → Wallet associations
6. ⏳ **Pending**: Test payment flow with real Locus API

---

**Status**: ✅ Mapping defined. Need Policy Group IDs from Locus Dashboard.

