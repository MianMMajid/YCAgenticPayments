# Locus Integration Status & Implementation Plan

## Current Status Analysis

### ✅ What Already Exists

1. **Project Structure**
   - ✅ `services/` directory exists (23 service files)
   - ✅ `agents/` directory exists (6 agent files)
   - ✅ `api/main.py` - FastAPI application entry point
   - ✅ `config/settings.py` - Settings management with Pydantic
   - ✅ Demo infrastructure (`demo/` directory with mock services)

2. **Existing Agents**
   - ✅ `agents/title_search_agent.py` - Title search agent
   - ✅ `agents/inspection_agent.py` - Inspection agent
   - ✅ `agents/appraisal_agent.py` - Appraisal agent
   - ✅ `agents/lending_agent.py` - Lending/underwriting agent

3. **Existing Services**
   - ✅ `services/smart_contract_wallet_manager.py` - Wallet management
   - ✅ `services/agentic_stripe_client.py` - Payment client
   - ✅ `services/blockchain_client.py` - Blockchain integration
   - ✅ `demo/mock_service_client.py` - Mock x402 client (for demo)

4. **Configuration**
   - ✅ `config/settings.py` - Settings class with environment variable loading
   - ✅ `.env` file support (via Pydantic BaseSettings)

### ❌ What's Missing (From Guide)

#### New Files Needed (4 files)

1. ❌ `services/locus_wallet_manager.py` - **NOT EXISTS**
   - Purpose: Manage Locus blockchain wallet
   - Status: **NEEDS CREATION**

2. ❌ `services/locus_integration.py` - **NOT EXISTS**
   - Purpose: Main Locus API integration
   - Status: **NEEDS CREATION**

3. ❌ `services/locus_payment_handler.py` - **NOT EXISTS**
   - Purpose: Process payments through Locus
   - Status: **NEEDS CREATION**

4. ❌ `services/x402_protocol_handler.py` - **NOT EXISTS**
   - Purpose: Handle x402 payment protocol
   - Status: **NEEDS CREATION**
   - Note: Similar functionality exists in `demo/mock_service_client.py` but needs production version

#### Files to Update (5 files)

1. ⚠️ `api/main.py` - **EXISTS BUT NEEDS UPDATE**
   - Current: FastAPI app with existing routes
   - Needed: Add Locus initialization on startup
   - Status: **NEEDS UPDATE**

2. ⚠️ `agents/title_search_agent.py` - **EXISTS BUT NEEDS UPDATE**
   - Current: Uses mock services or AI mocks
   - Needed: Integrate Locus payment handler
   - Status: **NEEDS UPDATE**

3. ⚠️ `agents/inspection_agent.py` - **EXISTS BUT NEEDS UPDATE**
   - Current: Uses mock services or AI mocks
   - Needed: Integrate Locus payment handler
   - Status: **NEEDS UPDATE**

4. ⚠️ `agents/appraisal_agent.py` - **EXISTS BUT NEEDS UPDATE**
   - Current: Uses mock services or AI mocks
   - Needed: Integrate Locus payment handler
   - Status: **NEEDS UPDATE**

5. ⚠️ `agents/lending_agent.py` - **EXISTS BUT NEEDS UPDATE**
   - Current: Uses mock services or AI mocks
   - Needed: Integrate Locus payment handler
   - Status: **NEEDS UPDATE**
   - Note: Guide mentions `underwriting_agent.py` but actual file is `lending_agent.py`

#### Configuration Updates Needed

1. ⚠️ `config/settings.py` - **EXISTS BUT NEEDS UPDATE**
   - Current: Has Agentic Stripe, blockchain settings
   - Needed: Add Locus-specific settings:
     - `locus_wallet_address`
     - `locus_wallet_private_key`
     - `locus_chain_id`
     - `locus_api_key`
     - `locus_policy_title_id`
     - `locus_policy_inspection_id`
     - `locus_policy_appraisal_id`
     - `locus_policy_underwriting_id`
     - `locus_agent_title_id` / `locus_agent_title_key`
     - `locus_agent_inspection_id` / `locus_agent_inspection_key`
     - `locus_agent_appraisal_id` / `locus_agent_appraisal_key`
     - `locus_agent_underwriting_id` / `locus_agent_underwriting_key`
     - `agent_title_budget`, `agent_inspection_budget`, etc.
     - `demo_mode`, `use_mock_services`
   - Status: **NEEDS UPDATE**

2. ⚠️ `.env` file - **NEEDS VERIFICATION**
   - Status: **NEEDS CHECK** - Verify all Locus IDs are present

---

## Implementation Plan

### Phase 1: Create New Service Files (4 files)

#### 1.1 Create `services/locus_wallet_manager.py`
- **Status**: ❌ Missing
- **Priority**: High
- **Dependencies**: None
- **Estimated Time**: 20 min

#### 1.2 Create `services/locus_integration.py`
- **Status**: ❌ Missing
- **Priority**: High
- **Dependencies**: `locus_wallet_manager.py`
- **Estimated Time**: 25 min

#### 1.3 Create `services/locus_payment_handler.py`
- **Status**: ❌ Missing
- **Priority**: High
- **Dependencies**: `locus_integration.py`
- **Estimated Time**: 25 min

#### 1.4 Create `services/x402_protocol_handler.py`
- **Status**: ❌ Missing
- **Priority**: Medium
- **Dependencies**: `locus_payment_handler.py`
- **Estimated Time**: 20 min
- **Note**: Can reference `demo/mock_service_client.py` for x402 flow

### Phase 2: Update Configuration (2 files)

#### 2.1 Update `config/settings.py`
- **Status**: ⚠️ Needs update
- **Priority**: High
- **Dependencies**: None
- **Estimated Time**: 15 min
- **Action**: Add all Locus-related settings fields

#### 2.2 Verify/Update `.env` file
- **Status**: ⚠️ Needs verification
- **Priority**: High
- **Dependencies**: None
- **Estimated Time**: 10 min
- **Action**: Ensure all Locus IDs from guide are present

### Phase 3: Update Main Application (1 file)

#### 3.1 Update `api/main.py`
- **Status**: ⚠️ Needs update
- **Priority**: High
- **Dependencies**: All Phase 1 files
- **Estimated Time**: 15 min
- **Action**: Add Locus initialization function and call on startup

### Phase 4: Update Agents (4 files)

#### 4.1 Update `agents/title_search_agent.py`
- **Status**: ⚠️ Needs update
- **Priority**: High
- **Dependencies**: Phase 1-3 complete
- **Estimated Time**: 20 min
- **Action**: Integrate Locus payment handler in `_perform_title_search()`

#### 4.2 Update `agents/inspection_agent.py`
- **Status**: ⚠️ Needs update
- **Priority**: High
- **Dependencies**: Phase 1-3 complete
- **Estimated Time**: 20 min
- **Action**: Integrate Locus payment handler in `_perform_inspection()`

#### 4.3 Update `agents/appraisal_agent.py`
- **Status**: ⚠️ Needs update
- **Priority**: High
- **Dependencies**: Phase 1-3 complete
- **Estimated Time**: 20 min
- **Action**: Integrate Locus payment handler in `_perform_appraisal()`

#### 4.4 Update `agents/lending_agent.py`
- **Status**: ⚠️ Needs update
- **Priority**: High
- **Dependencies**: Phase 1-3 complete
- **Estimated Time**: 20 min
- **Action**: Integrate Locus payment handler in `_perform_lending_verification()`
- **Note**: Guide calls it `underwriting_agent.py` but file is `lending_agent.py`

---

## Path Mapping (Guide → Actual)

The guide uses `counter_ai/` prefix but actual structure is different:

| Guide Path | Actual Path | Status |
|------------|-------------|--------|
| `counter_ai/services/locus_wallet_manager.py` | `services/locus_wallet_manager.py` | ❌ Missing |
| `counter_ai/services/locus_integration.py` | `services/locus_integration.py` | ❌ Missing |
| `counter_ai/services/locus_payment_handler.py` | `services/locus_payment_handler.py` | ❌ Missing |
| `counter_ai/services/x402_protocol_handler.py` | `services/x402_protocol_handler.py` | ❌ Missing |
| `counter_ai/app.py` | `api/main.py` | ⚠️ Exists, needs update |
| `counter_ai/agents/title_search_agent.py` | `agents/title_search_agent.py` | ⚠️ Exists, needs update |
| `counter_ai/agents/inspection_agent.py` | `agents/inspection_agent.py` | ⚠️ Exists, needs update |
| `counter_ai/agents/appraisal_agent.py` | `agents/appraisal_agent.py` | ⚠️ Exists, needs update |
| `counter_ai/agents/underwriting_agent.py` | `agents/lending_agent.py` | ⚠️ Exists, needs update |

---

## Key Differences from Guide

1. **Main Entry Point**: Guide says `app.py`, actual is `api/main.py` (FastAPI)
2. **Agent Name**: Guide says `underwriting_agent.py`, actual is `lending_agent.py`
3. **Path Prefix**: Guide uses `counter_ai/`, actual has no prefix
4. **Framework**: Guide seems to assume Flask, actual uses FastAPI
5. **Settings**: Already uses Pydantic BaseSettings (good!)

---

## Implementation Checklist

### New Files (4)
- [ ] `services/locus_wallet_manager.py`
- [ ] `services/locus_integration.py`
- [ ] `services/locus_payment_handler.py`
- [ ] `services/x402_protocol_handler.py`

### Configuration (2)
- [ ] Update `config/settings.py` with Locus settings
- [ ] Verify/Update `.env` with all Locus IDs

### Main App (1)
- [ ] Update `api/main.py` with Locus initialization

### Agents (4)
- [ ] Update `agents/title_search_agent.py`
- [ ] Update `agents/inspection_agent.py`
- [ ] Update `agents/appraisal_agent.py`
- [ ] Update `agents/lending_agent.py`

### Testing
- [ ] Test Locus initialization on startup
- [ ] Test agent payment flows
- [ ] Verify x402 protocol handling
- [ ] Test with mock services

---

## Estimated Timeline

- **Phase 1** (4 new files): ~90 minutes
- **Phase 2** (2 config files): ~25 minutes
- **Phase 3** (1 main file): ~15 minutes
- **Phase 4** (4 agent files): ~80 minutes
- **Testing**: ~30 minutes

**Total**: ~4 hours

---

## Next Steps

1. ✅ **DONE**: Analysis complete
2. ⏭️ **NEXT**: Create the 4 new service files
3. ⏭️ **THEN**: Update configuration
4. ⏭️ **THEN**: Update main app
5. ⏭️ **THEN**: Update agents
6. ⏭️ **FINALLY**: Test integration

---

## Notes

- The existing `demo/mock_service_client.py` can serve as reference for x402 flow
- The existing `services/smart_contract_wallet_manager.py` shows wallet management patterns
- FastAPI startup events should be used instead of Flask-style initialization
- Consider using FastAPI's `@app.on_event("startup")` for Locus initialization

