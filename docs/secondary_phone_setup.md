# Secondary Phone Number Setup Guide

## Overview

For the viewing scheduler demo, Counter needs to call listing agents to request property showings. To simulate this in a demo environment, you need a secondary phone number that can receive calls from Counter.

## Options

### Option 1: Google Voice (Recommended for Quick Demo)

**Pros**: Free, quick setup, voicemail transcription
**Cons**: US only, requires Google account

**Setup Steps**:
1. Go to [voice.google.com](https://voice.google.com)
2. Sign up for a free Google Voice number
3. Choose a local Baltimore area code (410, 443, or 667)
4. Configure settings:
   - Enable voicemail
   - Set to "Do not disturb" (all calls go to voicemail)
   - Enable email notifications for voicemails
5. Test by calling the number from your phone

**Demo Usage**:
- Counter will call this number when scheduling viewings
- Voicemail will capture the viewing request message
- You can play back the voicemail to verify the message content
- Email notifications let you know when Counter called

**Example Voicemail Message**:
```
Hi, this is Counter calling on behalf of my client Demo User. 
They're interested in viewing the property at 123 Monument Street 
on Saturday, November 16th at 2:00 PM. The buyer is pre-approved 
for $500,000. Please call back at 410-555-1234 or email 
demo@counter.app to confirm. Thank you!
```

---

### Option 2: Twilio Programmable Voice

**Pros**: Professional, can automate responses, logs all calls
**Cons**: Costs ~$1/month for number + per-minute charges

**Setup Steps**:
1. Sign up at [twilio.com](https://www.twilio.com) (free trial available)
2. Purchase a phone number ($1/month)
3. Configure TwiML webhook to handle incoming calls:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">
        Thank you for calling about the property viewing. 
        This is a demo number. Your request has been received. 
        We'll confirm the appointment shortly.
    </Say>
    <Record maxLength="120" transcribe="true" 
            transcribeCallback="https://your-domain.com/webhooks/twilio-transcribe"/>
    <Say>Thank you. Goodbye.</Say>
</Response>
```

4. Set up webhook endpoint to receive call logs and transcriptions
5. Test the number

**Demo Usage**:
- Counter calls the Twilio number
- Automated message plays acknowledging the viewing request
- Call is recorded and transcribed
- You receive webhook with call details and transcription

---

### Option 3: Second Vapi Agent (Most Realistic)

**Pros**: Fully conversational, can handle back-and-forth, most realistic demo
**Cons**: Requires additional Vapi assistant setup

**Setup Steps**:

1. Create a new Vapi assistant called "Listing Agent Simulator"

2. Configure the assistant with this system prompt:
```
You are a listing agent receiving calls about property viewings. 
When someone calls to schedule a viewing:
1. Greet them professionally
2. Ask for the property address
3. Ask for the requested viewing time
4. Ask for the buyer's name and contact info
5. Confirm the appointment or suggest an alternative time
6. Thank them and end the call

Be friendly, professional, and efficient. Keep responses brief.
```

3. Set up a Twilio phone number connected to this Vapi assistant

4. Configure the assistant to log all conversations

5. Test by calling the number manually

**Demo Usage**:
- Counter calls the listing agent simulator
- The two AI agents have a natural conversation
- Viewing details are exchanged
- Appointment is confirmed
- You can review the conversation transcript afterward

**Example Conversation**:
```
Agent: "Hello, this is Sarah with Baltimore Realty. How can I help you?"

Counter: "Hi Sarah, I'm calling on behalf of my client Demo User about 
         scheduling a viewing for 123 Monument Street."

Agent: "Great! When would your client like to see the property?"

Counter: "They're interested in Saturday, November 16th at 2 PM."

Agent: "Let me check... Yes, that works! Can I get your client's name 
       and contact information?"

Counter: "Sure, it's Demo User, phone 410-555-1234, email demo@counter.app. 
         They're pre-approved for $500,000."

Agent: "Perfect! I've got you scheduled for Saturday at 2 PM. I'll send 
       a confirmation email. Is there anything else?"

Counter: "No, that's all. Thank you!"

Agent: "You're welcome! See you Saturday!"
```

---

### Option 4: Manual Testing (Best for Live Demo)

**Pros**: Most control, can improvise, shows human-AI interaction
**Cons**: Requires a person to be available

**Setup Steps**:
1. Use your personal phone or a team member's phone
2. Create a simple script for the "listing agent" to follow
3. Have the person answer when Counter calls
4. Follow the script to confirm the viewing

**Listing Agent Script**:
```
[Phone rings]

Agent: "Hello, this is [Your Name] with [Brokerage]. How can I help you?"

[Counter introduces itself and requests viewing]

Agent: "Great! Let me check the schedule... Yes, [requested time] works 
       perfectly. Can I get the buyer's name and contact information?"

[Counter provides details]

Agent: "Wonderful! I have [Buyer Name] scheduled for [Time] at [Address]. 
       I'll send a confirmation email to [Email]. Is there anything else 
       I can help with?"

[Counter says no]

Agent: "Perfect! Looking forward to showing the property. Have a great day!"
```

**Demo Usage**:
- Most realistic for live demos
- Shows how Counter interacts with real humans
- Can handle unexpected questions or scenarios
- Demonstrates Counter's conversational abilities

---

## Configuration in Counter

Once you have your secondary phone number, update the demo script:

### In `DEMO_SCRIPT.md`:
```markdown
## Secondary Phone Number
- **Number**: [Your secondary number]
- **Type**: [Google Voice / Twilio / Vapi Agent / Manual]
- **Purpose**: Receives viewing request calls from Counter
```

### In Vapi Assistant Configuration:
If using Twilio for outbound calls, configure in `vapi_complete_config.json`:
```json
{
  "telephony": {
    "provider": "twilio",
    "outboundNumber": "+14105551234"
  }
}
```

### In Demo Environment Variables:
```bash
# .env
DEMO_AGENT_PHONE="+14105559999"  # Your secondary number
DEMO_MODE=true
```

---

## Testing the Setup

### Test 1: Manual Call
1. Call the secondary number from your phone
2. Verify it answers/goes to voicemail correctly
3. Leave a test message
4. Confirm you receive the message/notification

### Test 2: Counter Integration
1. Run the demo data loader: `python scripts/load_demo_data.py`
2. Start a voice session with Counter
3. Say: "Schedule a viewing at 123 Monument Street for tomorrow at 2pm"
4. Verify Counter calls the secondary number
5. Check that the viewing request message is delivered

### Test 3: End-to-End Flow
1. Search for properties
2. Analyze risks
3. Schedule viewing (triggers call to secondary number)
4. Verify viewing request is logged in database
5. Confirm calendar event is created

---

## Troubleshooting

### Counter doesn't make the call
- Check Twilio credentials in environment variables
- Verify outbound calling is enabled in Twilio account
- Check Vapi telephony configuration
- Review error logs for API failures

### Call quality is poor
- Check internet connection stability
- Verify Twilio region settings match your location
- Test with different phone numbers
- Review Twilio call quality metrics

### Voicemail not received
- Check Google Voice notification settings
- Verify email address is correct
- Check spam folder
- Test by calling manually first

### Agent simulator doesn't respond correctly
- Review Vapi assistant system prompt
- Check conversation logs for errors
- Adjust temperature setting (try 0.7-0.9)
- Add more specific instructions to prompt

---

## Cost Estimates

| Option | Setup Cost | Monthly Cost | Per-Use Cost |
|--------|-----------|--------------|--------------|
| Google Voice | Free | Free | Free |
| Twilio | Free trial | ~$1 | ~$0.01/min |
| Vapi Agent | Free trial | ~$10 | ~$0.05/min |
| Manual | Free | Free | Free |

---

## Recommendations

**For Quick Demo (< 1 hour)**:
- Use Google Voice or Manual testing
- Fastest setup, no cost
- Good enough for proof of concept

**For Hackathon Demo (24-48 hours)**:
- Use Twilio with TwiML
- Professional appearance
- Automated logging
- Low cost

**For Production-Ready Demo**:
- Use Vapi Agent simulator
- Most realistic interaction
- Shows full AI capabilities
- Best for investor/customer demos

**For Live Presentation**:
- Use Manual testing with script
- Most control and flexibility
- Can handle unexpected questions
- Shows human-AI collaboration

---

## Next Steps

1. Choose your preferred option based on demo requirements
2. Set up the secondary phone number
3. Update demo configuration with the number
4. Test the setup end-to-end
5. Practice the demo flow
6. Prepare backup plan (manual testing) in case of technical issues

For questions or issues, refer to:
- Twilio docs: https://www.twilio.com/docs
- Vapi docs: https://docs.vapi.ai
- Google Voice help: https://support.google.com/voice
