# Dashboard Configuration Checklist

**Two critical dashboard configurations needed for your hackathon demo**

---

## 1. ✅ SendGrid - Verify Sender Email

**Why**: SendGrid requires you to verify a sender email address before you can send emails. Without this, emails to listing agents will fail.

**Steps**:

1. **Go to SendGrid Dashboard**
   - Visit: https://app.sendgrid.com/
   - Log in with your account

2. **Navigate to Sender Authentication**
   - Click **Settings** → **Sender Authentication**
   - Or go directly: https://app.sendgrid.com/settings/sender_auth

3. **Verify Single Sender**
   - Click **"Verify a Single Sender"** (easiest for hackathon)
   - Fill out the form:
     - **From Email**: Use your email (e.g., `your-email@gmail.com`)
     - **From Name**: "Counter AI Real Estate"
     - **Reply To**: Same as From Email
     - **Company Address**: Your address
     - **City, State, Zip**: Your location
     - **Country**: Your country
   - Click **"Create"**

4. **Verify Email**
   - Check your email inbox
   - Click the verification link from SendGrid
   - ✅ **Status should change to "Verified"**

5. **Update Your Code** (if needed)
   - Make sure your code uses the verified email as the "from" address
   - Check `services/email_client.py` - it should use the verified email

**Time Required**: 2-3 minutes

**Status Check**: 
- Go to https://app.sendgrid.com/settings/sender_auth
- You should see your sender with a green "Verified" badge

---

## 2. ✅ Google Calendar API - Enable in Google Cloud Console

**Why**: The Google Calendar API must be enabled in your Google Cloud project before OAuth will work. Without this, calendar scheduling will fail.

**Steps**:

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Log in with your Google account

2. **Select Your Project**
   - If you don't have a project, create one:
     - Click the project dropdown at the top
     - Click **"New Project"**
     - Name it: "Counter AI Real Estate"
     - Click **"Create"**

3. **Enable Google Calendar API**
   - In the left sidebar, click **"APIs & Services"** → **"Library"**
   - Or go directly: https://console.cloud.google.com/apis/library
   - Search for **"Google Calendar API"**
   - Click on **"Google Calendar API"**
   - Click **"Enable"** button
   - ✅ Wait for it to show "API enabled"

4. **Verify OAuth Credentials**
   - Go to **"APIs & Services"** → **"Credentials"**
   - Or: https://console.cloud.google.com/apis/credentials
   - You should see your OAuth 2.0 Client ID (the one you already have)
   - If not, create one:
     - Click **"Create Credentials"** → **"OAuth 2.0 Client ID"**
     - Application type: **"Web application"**
     - Name: "Counter AI Calendar"
     - Authorized redirect URIs: 
       - `https://ycnov15googleoauth.ngrok.app/api/auth/callback/google`
       - (Add your production URL when ready)
     - Click **"Create"**
     - Copy the Client ID and Client Secret

5. **Verify Scopes**
   - Make sure your OAuth consent screen includes:
     - `https://www.googleapis.com/auth/calendar`
     - `https://www.googleapis.com/auth/calendar.events`
   - Go to **"APIs & Services"** → **"OAuth consent screen"**
   - Add these scopes if not already added

**Time Required**: 5-10 minutes

**Status Check**:
- Go to https://console.cloud.google.com/apis/library/calendar-json.googleapis.com
- Should show "API enabled" with a green checkmark

---

## Quick Verification Commands

After completing both configurations, test them:

### Test SendGrid
```bash
# This should work if sender is verified
curl -X POST https://api.sendgrid.com/v3/mail/send \
  -H "Authorization: Bearer YOUR_SENDGRID_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "personalizations": [{"to": [{"email": "test@example.com"}]}],
    "from": {"email": "YOUR_VERIFIED_EMAIL@example.com"},
    "subject": "Test",
    "content": [{"type": "text/plain", "value": "Test email"}]
  }'
```

### Test Google Calendar API
```bash
# Check if API is enabled (requires OAuth token)
# This is usually done through your app's OAuth flow
```

---

## Summary

| Service | Dashboard | Action | Time | Status |
|---------|-----------|--------|------|--------|
| **SendGrid** | https://app.sendgrid.com/ | Verify sender email | 2-3 min | ⚠️ **DO THIS** |
| **Google Calendar** | https://console.cloud.google.com/ | Enable Calendar API | 5-10 min | ⚠️ **DO THIS** |

---

## After Configuration

Once both are configured:

1. ✅ **SendGrid**: Emails to listing agents will work
2. ✅ **Google Calendar**: Calendar scheduling will work
3. ✅ **VAPI Tools**: Already created (4 tools ready)
4. ✅ **Backend**: Should be running on ngrok

**You're ready for the demo!** 🎉

---

## Troubleshooting

### SendGrid: "Sender not verified"
- Check: https://app.sendgrid.com/settings/sender_auth
- Make sure you clicked the verification link in your email
- Wait 1-2 minutes after clicking for status to update

### Google Calendar: "API not enabled"
- Check: https://console.cloud.google.com/apis/library/calendar-json.googleapis.com
- Make sure you clicked "Enable" and it shows "API enabled"
- Refresh the page if status doesn't update

### OAuth: "Invalid redirect URI"
- Make sure your ngrok URL is added to Authorized redirect URIs
- Format: `https://ycnov15googleoauth.ngrok.app/api/auth/callback/google`
- No trailing slash!

---

**Last Updated**: November 2024

