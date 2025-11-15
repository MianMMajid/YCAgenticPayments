# VAPI Update Guide - Exact Steps

**What you need to update in VAPI for your hackathon demo**

---

## Current ngrok URLs You Have

1. ✅ **DocuSign Webhook**: `https://ycnov15.ngrok.app`
2. ✅ **Google OAuth**: `https://ycnov15googleoauth.ngrok.app`
3. ⚠️ **Main Backend API**: **NEED TO CREATE** (new ngrok tunnel)

---

## Step 1: Create Main Backend ngrok URL

You need a **third ngrok URL** for your main backend API (where VAPI will call your tools).

### Option A: If Backend is Running Locally

```bash
# Terminal 1: Start your backend
cd /Users/omarramadan/Desktop/code/realtorAgent
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Create new ngrok tunnel
ngrok http 8000

# Copy the URL (e.g., https://abc123.ngrok.io)
# This is your MAIN BACKEND URL
```

### Option B: If Using Vercel

```bash
vercel --prod
# Get your Vercel URL (e.g., https://realtor-agent.vercel.app)
```

**For Hackathon**: Use ngrok for speed.

---

## Step 2: Update VAPI Tool URLs

### Method 1: Via VAPI Dashboard (Recommended)

1. **Go to**: https://dashboard.vapi.ai
2. **Open your Counter AI assistant**
3. **Navigate to**: "Functions" or "Tools" tab
4. **Update these 4 tool URLs**:

Replace `https://your-deployment-url.vercel.app` with your **main backend ngrok URL**:

| Tool Name | Current URL | Update To |
|-----------|------------|-----------|
| `search_properties` | `https://your-deployment-url.vercel.app/tools/search` | `https://YOUR-NGROK-URL.ngrok.io/tools/search` |
| `analyze_risk` | `https://your-deployment-url.vercel.app/tools/analyze-risk` | `https://YOUR-NGROK-URL.ngrok.io/tools/analyze-risk` |
| `schedule_viewing` | `https://your-deployment-url.vercel.app/tools/schedule` | `https://YOUR-NGROK-URL.ngrok.io/tools/schedule` |
| `draft_offer` | `https://your-deployment-url.vercel.app/tools/draft-offer` | `https://YOUR-NGROK-URL.ngrok.io/tools/draft-offer` |

**Example** (if your ngrok URL is `https://abc123.ngrok.io`):
- `search_properties`: `https://abc123.ngrok.io/tools/search`
- `analyze_risk`: `https://abc123.ngrok.io/tools/analyze-risk`
- `schedule_viewing`: `https://abc123.ngrok.io/tools/schedule`
- `draft_offer`: `https://abc123.ngrok.io/tools/draft-offer`

5. **Save** the assistant configuration

---

### Method 2: Update Config File and Re-import

1. **Update `vapi_tools_config.json`**:

Replace all instances of `https://your-deployment-url.vercel.app` with your ngrok URL:

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "search_properties",
        ...
      },
      "server": {
        "url": "https://YOUR-NGROK-URL.ngrok.io/tools/search",
        "method": "POST"
      }
    },
    {
      "type": "function",
      "function": {
        "name": "analyze_risk",
        ...
      },
      "server": {
        "url": "https://YOUR-NGROK-URL.ngrok.io/tools/analyze-risk",
        "method": "POST"
      }
    },
    {
      "type": "function",
      "function": {
        "name": "schedule_viewing",
        ...
      },
      "server": {
        "url": "https://YOUR-NGROK-URL.ngrok.io/tools/schedule",
        "method": "POST"
      }
    },
    {
      "type": "function",
      "function": {
        "name": "draft_offer",
        ...
      },
      "server": {
        "url": "https://YOUR-NGROK-URL.ngrok.io/tools/draft-offer",
        "method": "POST"
      }
    }
  ]
}
```

2. **Re-import to VAPI**:
   - Go to VAPI dashboard
   - Import the updated `vapi_tools_config.json`
   - Or copy-paste the JSON into the Functions section

---

## Step 3: Verify Tool URLs Work

Test each endpoint manually:

```bash
# Replace YOUR-NGROK-URL with your actual ngrok URL

# Test search
curl -X POST https://YOUR-NGROK-URL.ngrok.io/tools/search \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Baltimore, MD",
    "max_price": 400000,
    "user_id": "test-user"
  }'

# Test health check
curl https://YOUR-NGROK-URL.ngrok.io/health
```

**Expected**: Both should return 200 OK

---

## Step 4: Test VAPI Call

1. **Call your VAPI phone number**
2. **Say**: "Find me a house in Baltimore under $400,000"
3. **Verify**: AI responds and searches properties

---

## Quick Reference: All Your URLs

### For VAPI Tools (Main Backend)
- **URL**: `https://YOUR-NGROK-URL.ngrok.io` (create this)
- **Endpoints**:
  - `/tools/search`
  - `/tools/analyze-risk`
  - `/tools/schedule`
  - `/tools/draft-offer`

### For Webhooks (Already Configured)
- **DocuSign**: `https://ycnov15.ngrok.app/webhooks/docusign`
- **Google OAuth**: `https://ycnov15googleoauth.ngrok.app/api/auth/callback/google`

---

## Summary

**What to do**:
1. ✅ Create 1 more ngrok tunnel for main backend (port 8000)
2. ✅ Update 4 VAPI tool URLs with new ngrok URL
3. ✅ Test one phone call

**Time**: 5 minutes

---

**Last Updated**: November 2024

