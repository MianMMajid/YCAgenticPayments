# Autonomous Agents x402 Payment Demo

This demo showcases how the escrow agents autonomously handle x402 Payment Required responses from third-party services.

## What This Demo Shows

1. **Autonomous Payment Handling**: Agents automatically detect 402 responses, sign payments, and retry requests
2. **Real Service Integration**: Mock services that behave like real third-party APIs
3. **Parallel Execution**: All agents run simultaneously, just like in production
4. **Complete Flow**: From service call → 402 response → payment → success

## Quick Start

### Terminal 1: Start Mock Services

```bash
cd /Users/qubitmac/Desktop/Agentic\ Payments/realtorAIYC-main
pip install flask
python demo/mock_services.py
```

You should see:
```
============================================================
Mock x402 Payment Services
============================================================

Available Services:
  /landamerica/title-search      $ 1200.00 - LandAmerica Title Search
  /amerispec/inspection           $  500.00 - AmeriSpec Inspection
  /corelogic/valuation            $  400.00 - CoreLogic Valuation
  /fanniemae/verify               $    0.00 - Fannie Mae Verification

Starting server on http://localhost:5000
============================================================
```

### Terminal 2: Run Demo

```bash
cd /Users/qubitmac/Desktop/Agentic\ Payments/realtorAIYC-main
python demo/run_demo.py
```

## Expected Output

```
============================================================
AUTONOMOUS ESCROW AGENTS DEMO
============================================================

[Title Agent] Calling http://localhost:5000/landamerica/title-search
[Title Agent] Got 402 Payment Required
[Title Agent] Signed payment: 0x...
[Title Agent] Retrying with payment...
[Title Agent] SUCCESS - Title is CLEAR
[Title Agent] TX: 0xLandAmerica...

[Inspection Agent] Calling http://localhost:5000/amerispec/inspection
[Inspection Agent] Got 402 Payment Required
[Inspection Agent] Signed payment: 0x...
[Inspection Agent] Retrying with payment...
[Inspection Agent] SUCCESS - Scheduled for 2025-11-18
[Inspection Agent] TX: 0xAmeriSpec...

[Appraisal Agent] Calling http://localhost:5000/corelogic/valuation
[Appraisal Agent] Got 402 Payment Required
[Appraisal Agent] Signed payment: 0x...
[Appraisal Agent] Retrying with payment...
[Appraisal Agent] SUCCESS - Estimated $850,000
[Appraisal Agent] TX: 0xCoreLogic...

[Underwriting Agent] Calling http://localhost:5000/fanniemae/verify
[Underwriting Agent] Got 402 Payment Required
[Underwriting Agent] Signed payment: 0x...
[Underwriting Agent] Retrying with payment...
[Underwriting Agent] SUCCESS - PRE-APPROVED
[Underwriting Agent] TX: 0xFannieMae...

============================================================
DEMO RESULTS
============================================================

✓ 4/4 agents completed successfully
⏱  Total time: ~1 second

🎉 All agents completed autonomously!
   - All x402 payments verified
   - All services called successfully
   - All tasks completed
============================================================
```

## How It Works

### 1. Mock Services (`mock_services.py`)

Four Flask endpoints that simulate real third-party services:

- **`/landamerica/title-search`** - Returns 402, requires $1,200 payment
- **`/amerispec/inspection`** - Returns 402, requires $500 payment
- **`/corelogic/valuation`** - Returns 402, requires $400 payment
- **`/fanniemae/verify`** - Returns 402, requires signature (no amount)

Each service:
1. Returns 402 Payment Required on first call
2. Accepts payment signature and transaction hash
3. Returns service results after payment verification

### 2. Payment Helper (`payment_helper.py`)

Generates payment signatures and transaction hashes for demo purposes. In production, this would:
- Create blockchain transactions
- Sign with wallet private keys
- Return signed transaction hashes

### 3. Mock Service Client (`mock_service_client.py`)

Handles HTTP calls to mock services with automatic payment handling:
1. Makes initial request
2. Detects 402 response
3. Generates payment signature
4. Retries with payment
5. Returns service results

### 4. Updated Agents

All agents now call mock services instead of AI mocks:
- `TitleSearchAgent` → `/landamerica/title-search`
- `InspectionAgent` → `/amerispec/inspection`
- `AppraisalAgent` → `/corelogic/valuation`
- `LendingAgent` → `/fanniemae/verify`

## Key Features

✅ **Real x402 Handling**: Services actually return 402, not mocked responses  
✅ **Autonomous Payments**: Agents sign and submit payments automatically  
✅ **Parallel Execution**: All agents run simultaneously  
✅ **Complete Flow**: Full end-to-end demonstration  
✅ **Production-Ready Pattern**: Same pattern works with real services  

## Testing Individual Services

You can test services directly with curl:

```bash
# Test title search (will get 402)
curl -X POST http://localhost:5000/landamerica/title-search \
  -H "Content-Type: application/json" \
  -d '{"property_id": "test-123"}'

# Test with payment
curl -X POST http://localhost:5000/landamerica/title-search \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": "test-123",
    "payment_signature": "abc123",
    "payment_tx_hash": "0xtest456"
  }'
```

## Next Steps

To use with real services:
1. Replace `MockServiceClient` with real service clients
2. Update payment signing to use actual blockchain transactions
3. Configure service endpoints in environment variables
4. Add authentication/API keys as needed

