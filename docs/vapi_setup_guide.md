# Vapi Voice Interface Setup Guide

This guide walks through setting up the Vapi voice assistant for the Counter AI Real Estate Broker system.

## Overview

The Vapi configuration consists of:
1. **Assistant Configuration** - GPT-4o model, Cartesia voice, Deepgram transcription
2. **Tool Functions** - Four backend API endpoints for property operations
3. **Filler Phrases** - Conversational phrases to mask API latency
4. **Interruption Handling** - VAD settings for natural conversation flow
5. **Twilio Integration** - Phone number connection for voice calls

## Prerequisites

- Vapi account (https://vapi.ai)
- Twilio account with phone number (https://twilio.com)
- Deployed FastAPI backend (see main README.md)
- API keys configured in backend environment

## Step 1: Create Vapi Assistant

1. Log in to Vapi Dashboard (https://dashboard.vapi.ai)
2. Click "Create Assistant"
3. Configure the following settings:

### Model Configuration
```json
{
  "provider": "openai",
  "model": "gpt-4o",
  "temperature": 0.7
}
```

### System Prompt
Copy the system prompt from `vapi_assistant_config.json`:
```
You are Counter, an executive assistant helping a home buyer find and purchase property...
```

### Voice Configuration
```json
{
  "provider": "cartesia",
  "voiceId": "a0e99841-438c-4a64-b679-ae501e7d6091",
  "model": "sonic-english"
}
```

**Note**: The Cartesia Sonic voice provides ultra-low latency TTS (~80ms) which is critical for maintaining sub-1000ms response times.

### Transcriber Configuration
```json
{
  "provider": "deepgram",
  "model": "nova-2",
  "language": "en"
}
```

## Step 2: Add Tool Functions

In the Vapi assistant configuration, add the four tool functions. For each tool:

1. Click "Add Function"
2. Enter the function details from `vapi_tools_config.json`
3. **Important**: Update the `server.url` field with your actual deployment URL

### Tool 1: search_properties
- **Name**: `search_properties`
- **Description**: Search for properties matching the user's criteria
- **URL**: `https://YOUR-DEPLOYMENT.vercel.app/tools/search`
- **Method**: POST
- **Parameters**: See `vapi_tools_config.json`

### Tool 2: analyze_risk
- **Name**: `analyze_risk`
- **Description**: Analyze a property for potential red flags
- **URL**: `https://YOUR-DEPLOYMENT.vercel.app/tools/analyze-risk`
- **Method**: POST
- **Parameters**: See `vapi_tools_config.json`

### Tool 3: schedule_viewing
- **Name**: `schedule_viewing`
- **Description**: Schedule a property viewing
- **URL**: `https://YOUR-DEPLOYMENT.vercel.app/tools/schedule`
- **Method**: POST
- **Parameters**: See `vapi_tools_config.json`

### Tool 4: draft_offer
- **Name**: `draft_offer`
- **Description**: Generate a purchase offer document
- **URL**: `https://YOUR-DEPLOYMENT.vercel.app/tools/draft-offer`
- **Method**: POST
- **Parameters**: See `vapi_tools_config.json`

## Step 3: Configure Filler Phrases

In the assistant settings, find the "Filler Phrases" section and add:

```
Let me check the records on that...
Looking that up for you...
One moment while I verify...
Let me pull up those details...
Checking the database now...
Give me just a second to find that...
Let me search for that information...
Looking into that right now...
One moment, checking the listings...
Let me see what I can find...
```

These phrases will play during tool execution to maintain conversation flow.

## Step 4: Configure Interruption Handling

In the assistant settings, configure:

### Voice Activity Detection (VAD)
- **Enabled**: Yes
- **Sensitivity**: High
- **Silence Timeout**: 1.0 seconds

### Interruption Behavior
- **Stop on Interruption**: Yes
- **Resume After Interruption**: No
- **Clear Buffer on Interruption**: Yes

### Endpointing
- **Enabled**: Yes
- **Silence Duration**: 0.8 seconds

### Background Noise Suppression
- **Enabled**: Yes
- **Level**: Medium

## Step 5: Connect Twilio Phone Number

### In Twilio Console:
1. Go to https://console.twilio.com/
2. Navigate to Phone Numbers → Manage → Buy a number
3. Purchase a phone number (recommend US number for lowest latency)
4. Note your Account SID and Auth Token

### In Vapi Dashboard:
1. Go to "Phone Numbers" section
2. Click "Import Twilio Number"
3. Enter your Twilio Account SID and Auth Token
4. Select the phone number you purchased
5. Assign the Counter assistant to this number
6. Configure first message: "Hi, this is Counter, your real estate assistant. How can I help you find a home today?"

### Verify Configuration:
- Vapi will automatically configure the SIP trunk
- Twilio webhooks will be updated to point to Vapi
- No manual webhook configuration needed

## Step 6: Test the Integration

### Basic Call Test
1. Call the Twilio phone number
2. Verify you hear the first message
3. Say "Find me a house in Baltimore under 400k"
4. Verify the assistant calls the search tool and responds with properties

### Interruption Test
1. Call the assistant
2. While it's speaking, interrupt by saying something
3. Verify it stops immediately and processes your new input

### Tool Execution Test
Test each tool:
- **Search**: "Find homes in Baltimore under 400k"
- **Risk Analysis**: "Check that property for issues"
- **Schedule**: "Schedule a viewing for tomorrow at 2pm"
- **Offer**: "Make an offer for 350k cash"

### Audio Quality Test
- Check for echo, static, or distortion
- Verify latency feels natural (<1 second)
- Test from different phone types (mobile, landline)

## Step 7: Monitor and Optimize

### Vapi Dashboard Metrics
Monitor these metrics in the Vapi dashboard:
- Average response time (target: <1000ms)
- Tool execution success rate
- Call duration
- Interruption frequency

### Backend Monitoring
Check your FastAPI logs for:
- Tool execution times
- API errors
- Cache hit rates

### Optimization Tips
1. **If response time > 1s**: Check backend API latency, consider caching more aggressively
2. **If interruptions not working**: Increase VAD sensitivity
3. **If audio quality poor**: Check Twilio region matches Vapi region
4. **If tools failing**: Verify backend URLs are correct and accessible

## Configuration Files Reference

All configuration files are in the project root:
- `vapi_assistant_config.json` - Base assistant configuration
- `vapi_tools_config.json` - Tool function definitions
- `vapi_filler_phrases_config.json` - Filler phrases
- `vapi_interruption_config.json` - VAD and interruption settings
- `vapi_twilio_integration.json` - Twilio setup instructions

## Troubleshooting

### "Assistant not responding"
- Check that backend URLs are correct and accessible
- Verify API keys are configured in backend
- Check Vapi logs for errors

### "No audio on call"
- Verify Twilio webhook points to Vapi SIP endpoint
- Check Twilio account balance
- Verify phone number is assigned to assistant

### "High latency"
- Check backend response times
- Verify caching is working
- Consider using Redis for faster cache
- Check Twilio and Vapi regions match

### "Tools not executing"
- Verify backend endpoints return 200 status
- Check request/response format matches schema
- Review Vapi function logs for errors

### "Echo or audio issues"
- Enable echo cancellation in Twilio console
- Check for network issues
- Verify audio codec settings (PCMU, 8kHz)

## Production Checklist

Before going live:
- [ ] All tool URLs point to production backend
- [ ] Backend environment variables configured
- [ ] Twilio phone number purchased and connected
- [ ] First message configured
- [ ] All four tools tested successfully
- [ ] Interruption handling verified
- [ ] Audio quality tested from multiple devices
- [ ] Monitoring and logging enabled
- [ ] Error handling tested (API failures, invalid inputs)
- [ ] Call recording disabled (for privacy)

## Next Steps

After Vapi is configured:
1. Test end-to-end user flows
2. Gather feedback on conversation quality
3. Iterate on system prompt for better responses
4. Monitor metrics and optimize latency
5. Consider adding more filler phrases for variety

## Support

- Vapi Documentation: https://docs.vapi.ai
- Vapi Discord: https://discord.gg/vapi
- Twilio Support: https://support.twilio.com

