# OAuth Credentials Analysis

## Credentials Provided

- **Client ID**: `7ifti978u035o1intfmbuar8p9`
- **Client Secret**: `h67g7r27go70h4iba2t1e243f7lfr9sptuse39hbnsqe9i1j25i`
- **API Secret**: `locus_dev_KkxgbZKe9rGMtQL7zXyJGTd6sRrC_kwR`

## Findings from Testing

### 1. Correct Endpoint Found
✅ **Endpoint**: `https://api.paywithlocus.com/api/mcp/tools/send_to_address`

This endpoint:
- Returns 401 JSON error when using `X-API-Key` header only
- Error message: "Missing or invalid Authorization header"
- This confirms the endpoint exists and recognizes the request format

### 2. Authentication Requirements

The endpoint requires:
- **X-API-Key header** (for API key identification)
- **Authorization header** (format TBD)

### 3. Current Status

- ❌ OAuth token endpoint not found (tried multiple endpoints)
- ❌ Direct API key authentication not working yet
- ✅ Endpoint structure confirmed
- ✅ Request format confirmed

## Next Steps

### Option 1: Find OAuth Endpoint via Browser DevTools

1. Open Locus Dashboard
2. Open DevTools → Network tab
3. Make a payment
4. Find the OAuth token request
5. Copy the OAuth endpoint URL

### Option 2: Use API Key to Get OAuth Token

According to MCP spec, API keys are validated by backend and return associated OAuth client scopes. We might need to:

1. Call an endpoint with API key to get OAuth token
2. Use that token in Authorization header
3. Include X-API-Key header for identification

### Option 3: Different Auth Format

The Authorization header might need:
- Different format (not Bearer)
- API key in different position
- Additional headers

## Recommendation

**Use Browser DevTools** to find:
1. The exact OAuth token endpoint
2. The exact Authorization header format
3. Any additional required headers

Once we have this, we can update the code to use OAuth properly.

