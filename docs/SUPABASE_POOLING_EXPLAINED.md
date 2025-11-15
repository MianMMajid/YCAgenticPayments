# Supabase Connection Pooling vs Session Pooling

## Quick Answer

**No, they're not the same!** Supabase's "Connection Pooling" (port 6543) uses **Transaction Mode Pooling**, which is different from Session Pooling.

---

## The Three Types

### 1. Direct Connection (Port 5432)
- **What it is**: Direct connection to PostgreSQL
- **Connection**: One connection per client, held for entire session
- **Limitations**: 
  - Limited to ~200 connections total
  - Not ideal for serverless (many concurrent functions)
- **Use case**: Development, simple apps

### 2. Session Pooling
- **What it is**: Each client gets a dedicated server connection for the entire session
- **Connection**: One-to-one mapping (client connection → server connection)
- **When client disconnects**: Server connection returns to pool
- **Supports**: All PostgreSQL features
- **Limitations**: Still limited by number of server connections
- **Use case**: Traditional applications with persistent connections

### 3. Transaction Pooling (What Supabase Port 6543 Uses)
- **What it is**: Connections are shared across transactions
- **Connection**: Many client connections → fewer server connections
- **How it works**: 
  - Client connects to pooler
  - Pooler assigns a server connection only during a transaction
  - After transaction completes, connection returns to pool
  - Next transaction can use a different server connection
- **Supports**: Most PostgreSQL features (some limitations)
- **Benefits**: 
  - Can handle thousands of concurrent clients
  - Perfect for serverless functions
  - More efficient resource usage
- **Use case**: **Serverless, Vercel functions, high concurrency**

---

## What Supabase Offers

### Port 5432: Direct Connection
```
postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
```
- Direct PostgreSQL connection
- Limited to ~200 connections
- Good for: Development, simple apps

### Port 6543: Transaction Mode Pooling (Recommended)
```
postgresql://postgres.[ref]:[password]@[region].pooler.supabase.com:6543/postgres
```
- Uses Supavisor (Supabase's pooler)
- **Transaction mode pooling** (not session pooling)
- Can handle thousands of concurrent connections
- **Best for: Serverless, Vercel, production**

---

## Why Transaction Mode for Serverless?

**Serverless functions (like Vercel) are short-lived:**
1. Function starts → connects to database
2. Executes transaction(s)
3. Function ends → connection closes

**Transaction pooling is perfect because:**
- ✅ Connections are only held during transactions
- ✅ Many functions can share fewer database connections
- ✅ No connection exhaustion
- ✅ Better for high concurrency

**Session pooling would be wasteful because:**
- ❌ Each function would hold a connection for its entire lifetime
- ❌ Connections would be idle most of the time
- ❌ Would hit connection limits quickly

---

## What Your Code Uses

Looking at your `models/database.py`:
```python
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)
```

This is **client-side connection pooling** (SQLAlchemy's pool). It works **on top of** Supabase's pooler:

```
Your App (SQLAlchemy Pool) 
  → Supabase Pooler (Transaction Mode)
    → PostgreSQL Database
```

**Two levels of pooling:**
1. **SQLAlchemy pool**: Manages connections in your application
2. **Supabase pooler**: Manages connections at the database level

---

## Summary

| Type | Port | Mode | Best For |
|------|------|------|----------|
| Direct | 5432 | Direct | Development |
| Session Pooling | N/A* | Session | Traditional apps |
| **Transaction Pooling** | **6543** | **Transaction** | **Serverless, Production** |

*Supabase doesn't offer session pooling as a separate option - port 6543 uses transaction mode.

---

## Recommendation

**Use Port 6543 (Transaction Pooling)** for:
- ✅ Production deployments
- ✅ Vercel serverless functions
- ✅ High concurrency
- ✅ Better resource efficiency

**Use Port 5432 (Direct)** for:
- ✅ Local development
- ✅ Simple scripts
- ✅ When you need full PostgreSQL features without any limitations

---

## References

- [Supabase Connection Pooling Docs](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Supavisor and Connection Terminology](https://supabase.com/docs/guides/troubleshooting/supavisor-and-connection-terminology-explained)

