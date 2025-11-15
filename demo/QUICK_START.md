# Quick Start Guide

## Step 1: Install Flask (if not already installed)

```bash
pip install flask
```

## Step 2: Start Mock Services (Terminal 1)

```bash
cd /Users/qubitmac/Desktop/Agentic\ Payments/realtorAIYC-main
python demo/mock_services.py
```

Keep this terminal running. You should see:
```
Starting server on http://localhost:5000
```

## Step 3: Run Demo (Terminal 2)

In a new terminal:

```bash
cd /Users/qubitmac/Desktop/Agentic\ Payments/realtorAIYC-main
python demo/run_demo.py
```

## What You'll See

The demo will show:
- Each agent calling its service
- Getting 402 Payment Required
- Signing payment automatically
- Retrying with payment
- Success with transaction hash

All 4 agents complete in ~1 second!

## Troubleshooting

**Error: "Connection refused"**
- Make sure mock_services.py is running in Terminal 1
- Check that it's listening on port 5000

**Error: "Module not found"**
- Make sure you're in the project root directory
- Check that demo/ directory exists

**Error: "Flask not found"**
- Run: `pip install flask`

