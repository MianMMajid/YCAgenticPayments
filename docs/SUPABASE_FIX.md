# Fixing Supabase Database Connection

## Current Issue
DNS resolution error: `could not translate host name "db.jyfggchbybxamuukngzm.supabase.co" to address`

## Possible Causes & Solutions

### 1. Supabase Project is Paused (Most Likely)

**Free tier projects pause after 1 week of inactivity**

**Fix:**
1. Go to https://app.supabase.com
2. Log in to your account
3. Find your project: `jyfggchbybxamuukngzm`
4. If it shows "Paused", click "Restore" or "Resume"
5. Wait 1-2 minutes for the project to restart
6. Try connecting again

---

### 2. Use Connection Pooling URL (Recommended)

**Your current URL uses direct connection (port 5432)**
- Direct connections have connection limits
- Connection pooling is better for production

**Get Connection Pooling URL:**
1. Go to Supabase Dashboard → Your Project
2. Go to **Settings** → **Database**
3. Scroll to **Connection Pooling**
4. Copy the **Connection Pooling** URL (port **6543**)
5. Format: `postgresql://postgres.[ref]:[password]@[region].pooler.supabase.com:6543/postgres`

**Update your `.env` file:**
```bash
# Replace the DATABASE_URL with the pooling URL
DATABASE_URL=postgresql://postgres.jyfggchbybxamuukngzm:[YOUR_PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

---

### 3. Verify Project Reference ID

**Check if the project reference is correct:**
- Your reference: `jyfggchbybxamuukngzm`
- Verify in Supabase Dashboard → Project Settings → General
- The reference should match

---

### 4. Check Network/Firewall

**If project is active but still can't connect:**
1. Check if you're behind a corporate firewall
2. Try from a different network
3. Check if VPN is blocking the connection
4. Verify DNS settings

---

### 5. Test Connection Manually

**Test with psql:**
```bash
# Install psql if needed (macOS)
brew install postgresql

# Test connection
psql "postgresql://postgres:[PASSWORD]@db.jyfggchbybxamuukngzm.supabase.co:5432/postgres"
```

**Or test with Python:**
```python
import psycopg2
conn = psycopg2.connect("postgresql://postgres:[PASSWORD]@db.jyfggchbybxamuukngzm.supabase.co:5432/postgres")
print("✅ Connected!")
```

---

## Quick Fix Steps

### Step 1: Check Project Status
1. Visit: https://app.supabase.com/project/jyfggchbybxamuukngzm
2. Check if project is paused
3. If paused, click "Restore"

### Step 2: Get Connection Pooling URL
1. In Supabase Dashboard → Settings → Database
2. Find "Connection Pooling" section
3. Copy the URL (port 6543)
4. Update `.env` file

### Step 3: Update .env File
```bash
# Edit .env file
DATABASE_URL=postgresql://postgres.jyfggchbybxamuukngzm:DwdTuDn7MN0ZSOn3@[REGION].pooler.supabase.com:6543/postgres
```

Replace `[REGION]` with your actual region (e.g., `aws-0-us-east-1`)

### Step 4: Test Connection
```bash
python3 test_all_connections.py
```

---

## Connection URL Formats

### Direct Connection (Current - Port 5432)
```
postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

### Connection Pooling (Recommended - Port 6543)
```
postgresql://postgres.[PROJECT_REF]:[PASSWORD]@[REGION].pooler.supabase.com:6543/postgres
```

**Note:** Connection pooling URL format is different:
- Uses `postgres.[PROJECT_REF]` instead of `postgres`
- Uses `[REGION].pooler.supabase.com` instead of `db.[PROJECT_REF].supabase.co`
- Uses port `6543` instead of `5432`

---

## Still Not Working?

1. **Check Supabase Status Page**: https://status.supabase.com
2. **Verify Password**: Make sure password is correct (no extra spaces)
3. **Check Project Settings**: Ensure project hasn't been deleted
4. **Contact Support**: https://supabase.com/support

---

## After Fixing

Once connected, run database migrations:
```bash
# Run Alembic migrations
alembic upgrade head

# Or use the migration script
python3 scripts/migrate.py
```

