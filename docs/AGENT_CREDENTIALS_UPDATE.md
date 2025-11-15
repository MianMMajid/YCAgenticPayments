# Agent Credentials Update Summary

**Date**: November 15, 2025  
**Status**: ✅ **COMPLETED**

---

## Updated Credentials

### Title Search Agent
- **Agent ID**: `ooeju0aot520uv7dd77nr7d5r`
- **API Key**: `locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG`
- **Client ID**: `ooeju0aot520uv7dd77nr7d5r` (same as Agent ID)
- **Client Secret**: `16hestjsrtgu95e2nfg29riun1d20ic8rmr83frsduiscsp0vb22` (OAuth - not used with API Key auth)
- **Policy**: LandAmerica Title Verification Policy
- **Budget**: $0.03/day
- **Status**: Active

### Inspection Agent
- **Agent ID**: `2ss8gjcf4q8g05hueor4ftnuu7`
- **API Key**: `locus_dev_NeMbZAgJFwpWXIrGaiZQTWm-Fhnpsxfd`
- **Client ID**: `2ss8gjcf4q8g05hueor4ftnuu7` (same as Agent ID)
- **Client Secret**: `3e93u32rtla92lhr8aiqfcch47ftk2qtnbctpb519hfs7bmvtqf` (OAuth - not used with API Key auth)
- **Policy**: AmeriSpec Home Inspection Policy
- **Budget**: $0.012/day
- **Status**: Active

---

## Environment Variables Updated

The following variables have been added/updated in `.env`:

```bash
# Agent IDs & Keys
LOCUS_AGENT_TITLE_ID=ooeju0aot520uv7dd77nr7d5r
LOCUS_AGENT_TITLE_KEY=locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG
LOCUS_AGENT_INSPECTION_ID=2ss8gjcf4q8g05hueor4ftnuu7
LOCUS_AGENT_INSPECTION_KEY=locus_dev_NeMbZAgJFwpWXIrGaiZQTWm-Fhnpsxfd
```

---

## Authentication Method

**Current**: API Key Authentication  
**Alternative**: OAuth 2.0 (Client ID + Client Secret)

The system is configured to use **API Key authentication** (Static API Key). The OAuth credentials (Client ID + Client Secret) are available but not currently used. If you need to switch to OAuth authentication, you would need to:

1. Update the authentication method in the Locus integration code
2. Use Client ID and Client Secret instead of API Key
3. Implement OAuth token refresh logic

---

### Appraisal Agent
- **Agent ID**: `7qictfjj57f973mfp0i4ku209k`
- **API Key**: `locus_dev_y7wmTdasNBO4gCsFxWJnQ8bo0IROSOKk`
- **Client ID**: `7qictfjj57f973mfp0i4ku209k` (same as Agent ID)
- **Client Secret**: `o0g5crk2l8p1onfkmfcnv5ot9ha0n4dt97t83b7463aa4mvu7gb` (OAuth - not used with API Key auth)
- **Policy**: CoreLogic Property Valuation Policy
- **Budget**: $0.010/day
- **Status**: Active

### Underwriting Agent
- **Agent ID**: `27fqhc1mtsd97q63bddaqoutmv`
- **API Key**: `locus_dev_cRKUMxRuSSjqaQzRgdbdhm5Jz2-szqVl`
- **Client ID**: `27fqhc1mtsd97q63bddaqoutmv` (same as Agent ID)
- **Client Secret**: `12ejv3cbserimir6s5ks96br8jh70jrhmabejthi7irfe1920m3f` (OAuth - not used with API Key auth)
- **Policy**: Fannie Mae Loan Verification Policy
- **Budget**: $0.019/day
- **Status**: Active

---

## Environment Variables Updated

The following variables have been added/updated in `.env`:

```bash
# Agent IDs & Keys
LOCUS_AGENT_TITLE_ID=ooeju0aot520uv7dd77nr7d5r
LOCUS_AGENT_TITLE_KEY=locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG
LOCUS_AGENT_INSPECTION_ID=2ss8gjcf4q8g05hueor4ftnuu7
LOCUS_AGENT_INSPECTION_KEY=locus_dev_NeMbZAgJFwpWXIrGaiZQTWm-Fhnpsxfd
LOCUS_AGENT_APPRAISAL_ID=7qictfjj57f973mfp0i4ku209k
LOCUS_AGENT_APPRAISAL_KEY=locus_dev_y7wmTdasNBO4gCsFxWJnQ8bo0IROSOKk
LOCUS_AGENT_UNDERWRITING_ID=27fqhc1mtsd97q63bddaqoutmv
LOCUS_AGENT_UNDERWRITING_KEY=locus_dev_cRKUMxRuSSjqaQzRgdbdhm5Jz2-szqVl
```

---

## Still Needed

### Policy Group IDs
- [ ] **LOCUS_POLICY_TITLE_ID** (from Locus Dashboard)
- [ ] **LOCUS_POLICY_INSPECTION_ID** (from Locus Dashboard)
- [ ] **LOCUS_POLICY_APPRAISAL_ID** (from Locus Dashboard)
- [ ] **LOCUS_POLICY_UNDERWRITING_ID** (from Locus Dashboard)

---

## Verification

To verify the credentials are properly configured:

1. Check `.env` file contains the updated values
2. Restart the application to load new environment variables
3. Test with a demo transaction to verify agent authentication

---

## Next Steps

1. ✅ **Completed**: All 4 agent credentials added (Title, Inspection, Appraisal, Underwriting)
2. ⏳ **Pending**: Get Policy Group IDs from Locus Dashboard
3. ⏳ **Pending**: Update `.env` with Policy Group IDs
4. ⏳ **Pending**: Test full integration with all agents and real Locus API

---

## Security Notes

- ✅ API Keys are stored in `.env` file (not committed to git)
- ✅ Client Secrets are available but not used (OAuth not implemented)
- ⚠️ **Important**: Never commit `.env` file to version control
- ⚠️ **Important**: Rotate credentials if compromised
- ⚠️ **Important**: Use environment-specific credentials (dev/staging/prod)

---

**Update Completed**: November 15, 2025  
**Script Used**: `scripts/update_agent_credentials.py`

