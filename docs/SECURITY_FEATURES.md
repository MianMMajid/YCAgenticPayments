# Security Features Documentation

## Overview

The Intelligent Escrow Agents system implements comprehensive security measures to protect transactions, sensitive data, and wallet operations. This document describes all security features and how to configure them.

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [Data Encryption](#data-encryption)
3. [Smart Contract Security](#smart-contract-security)
4. [TLS/SSL Configuration](#tlsssl-configuration)
5. [Key Management](#key-management)

---

## Authentication & Authorization

### JWT-Based Authentication

All agents must authenticate using JWT tokens to access the API.

#### Agent Roles

The system supports the following agent roles:

- **ESCROW_AGENT**: Full control over transactions and wallet operations
- **BUYER_AGENT**: Can initiate transactions and view their own transactions
- **SELLER_AGENT**: Can view transactions they're involved in
- **TITLE_SEARCH_AGENT**: Can submit title search verifications
- **INSPECTION_AGENT**: Can submit inspection reports
- **APPRAISAL_AGENT**: Can submit appraisal reports
- **LENDING_AGENT**: Can submit lending verifications
- **ADMIN**: Full system access including agent management

#### Authentication Flow

1. **Register an Agent** (Admin only):
```bash
POST /auth/register
{
  "agent_id": "escrow_agent_001",
  "name": "Main Escrow Agent",
  "email": "escrow@example.com",
  "api_key": "your-secure-api-key",
  "role": "escrow_agent"
}
```

2. **Login**:
```bash
POST /auth/login
{
  "agent_id": "escrow_agent_001",
  "api_key": "your-secure-api-key"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "agent_id": "escrow_agent_001",
  "role": "escrow_agent"
}
```

3. **Use Token in Requests**:
```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Role-Based Access Control (RBAC)

Each role has specific permissions:

| Permission | Escrow | Buyer | Seller | Verification Agents | Admin |
|-----------|--------|-------|--------|---------------------|-------|
| Create Transaction | ✓ | ✓ | ✗ | ✗ | ✓ |
| Release Payment | ✓ | ✗ | ✗ | ✗ | ✓ |
| Submit Verification | ✗ | ✗ | ✗ | ✓ | ✓ |
| Execute Settlement | ✓ | ✗ | ✗ | ✗ | ✓ |
| Read Audit Trail | ✓ | ✓ | ✓ | ✓ | ✓ |
| Manage Agents | ✗ | ✗ | ✗ | ✗ | ✓ |

#### Wallet Access Control

**Critical**: Only Escrow Agents can trigger wallet operations (payments, settlements).

This is enforced at multiple levels:
- API endpoint authorization
- Service layer validation
- Audit logging of all wallet operations

---

## Data Encryption

### Encryption at Rest

Sensitive data is encrypted in the database using Fernet symmetric encryption.

#### Encrypted Fields

- **User Model**: `phone_number`, `email`, `google_calendar_token`
- **Agent Model**: `email`
- **Transaction Model**: `encrypted_metadata` (for PII and financial details)

#### Configuration

Set the encryption key in your environment:

```bash
# Generate a key
python scripts/generate_encryption_key.py

# Set in .env
ENCRYPTION_KEY=your-base64-encoded-key
```

**Important**: 
- Never commit the encryption key to version control
- Use the same key across all instances
- Changing the key will make existing encrypted data unreadable

#### Encrypting Sensitive Transaction Data

```python
from services.encryption_service import encryption_service

# Encrypt PII
pii_data = {
    "ssn": "123-45-6789",
    "bank_account": "1234567890",
    "drivers_license": "DL123456"
}
encrypted_pii = encryption_service.encrypt_pii(pii_data)

# Decrypt PII
decrypted_pii = encryption_service.decrypt_pii(encrypted_pii)
```

### Encryption in Transit

All API communications should use TLS 1.3.

#### TLS Configuration

```bash
# .env
TLS_ENABLED=true
TLS_CERT_FILE=/path/to/cert.pem
TLS_KEY_FILE=/path/to/key.pem
TLS_CA_FILE=/path/to/ca.pem  # Optional
```

#### Running with TLS

```python
# In production, Uvicorn will use TLS configuration
from config.tls_config import tls_config

ssl_config = tls_config.get_uvicorn_ssl_config()
uvicorn.run(app, host="0.0.0.0", port=8000, **ssl_config)
```

---

## Smart Contract Security

### Multi-Signature Requirements

Large settlements require multiple approvals before execution.

#### Configuration

```bash
POST /api/escrow/transactions/{transaction_id}/wallet/security-config
{
  "multi_sig_enabled": true,
  "multi_sig_threshold": 50000.00,  # Amount requiring multi-sig
  "required_approvers": 2            # Number of approvals needed
}
```

#### Approval Flow

1. **Initiate Operation** (automatically creates pending operation):
```bash
POST /api/escrow/transactions/{transaction_id}/settlement
```

2. **Approve Operation** (by each required approver):
```bash
POST /api/escrow/wallet-operations/{operation_id}/approve
```

3. **Execute** (automatically when approvals met):
The operation executes automatically once all approvals are received.

### Time Locks

Large fund releases are delayed to allow for review.

#### Configuration

```bash
POST /api/escrow/transactions/{transaction_id}/wallet/security-config
{
  "time_lock_enabled": true,
  "time_lock_threshold": 100000.00,    # Amount requiring time lock
  "time_lock_duration_hours": 24       # Delay in hours
}
```

#### How It Works

1. Operation is initiated
2. System calculates unlock time (current time + duration)
3. Operation cannot execute until unlock time is reached
4. All parties are notified of the pending operation

### Emergency Pause Circuit Breaker

Immediately halt all wallet operations in case of security incident.

#### Pause Wallet

```bash
POST /api/escrow/transactions/{transaction_id}/wallet/pause
{
  "reason": "Suspected fraudulent activity detected"
}
```

#### Resume Wallet

```bash
POST /api/escrow/transactions/{transaction_id}/wallet/resume
```

**Note**: Only Escrow Agents can pause/resume wallets.

### Wallet Operation Audit Trail

All wallet operations are logged for compliance and dispute resolution.

#### View Audit Trail

```bash
GET /api/escrow/transactions/{transaction_id}/wallet/audit-trail?limit=100
```

#### Audit Log Entries Include

- Operation type (PAYMENT, SETTLEMENT, PAUSE, RESUME)
- Agent who performed the action
- Timestamp
- Amount (if applicable)
- Approval status
- Additional details

---

## TLS/SSL Configuration

### Minimum TLS Version

The system enforces TLS 1.3 as the minimum version for all communications.

### Cipher Suites

Only strong cipher suites are allowed:
- ECDHE+AESGCM
- ECDHE+CHACHA20
- DHE+AESGCM
- DHE+CHACHA20

Weak ciphers (MD5, DSS, NULL) are explicitly disabled.

### Certificate Management

#### Development

For development, you can generate self-signed certificates:

```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

#### Production

Use certificates from a trusted Certificate Authority (CA):
- Let's Encrypt (free, automated)
- DigiCert
- Comodo
- GlobalSign

#### Certificate Renewal

Set up automatic renewal for Let's Encrypt:

```bash
certbot renew --deploy-hook "systemctl reload escrow-api"
```

---

## Key Management

### Local Key Management

By default, encryption keys are stored in environment variables.

```bash
ENCRYPTION_KEY=your-base64-encoded-key
```

### AWS KMS Integration

For production, integrate with AWS Key Management Service.

#### Setup

1. **Install AWS SDK**:
```bash
pip install boto3
```

2. **Create KMS Key**:
```bash
aws kms create-key --description "Escrow system encryption key"
```

3. **Configure Environment**:
```bash
KMS_ENABLED=true
KMS_KEY_ID=arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012
KMS_REGION=us-east-1
```

4. **Encrypt Data Key**:
```bash
aws kms encrypt --key-id $KMS_KEY_ID --plaintext fileb://data-key.txt
```

#### Benefits of KMS

- Centralized key management
- Automatic key rotation
- Audit trail of key usage
- Hardware security modules (HSM) backing
- Fine-grained access control via IAM

### Key Rotation

**Important**: Key rotation requires re-encrypting all data.

Process:
1. Generate new key
2. Decrypt all data with old key
3. Re-encrypt with new key
4. Update key in environment/KMS
5. Verify all data is accessible

---

## Security Best Practices

### 1. Environment Variables

Never commit sensitive values to version control:

```bash
# .env (add to .gitignore)
ENCRYPTION_KEY=...
DATABASE_URL=...
AGENTIC_STRIPE_API_KEY=...
BLOCKCHAIN_PRIVATE_KEY=...
```

### 2. API Key Management

- Generate strong, random API keys
- Rotate keys regularly (every 90 days)
- Use different keys for different environments
- Revoke compromised keys immediately

### 3. Database Security

- Use strong database passwords
- Enable SSL for database connections
- Restrict database access by IP
- Regular backups with encryption

### 4. Monitoring & Alerts

Set up alerts for:
- Failed authentication attempts
- Unauthorized access attempts
- Large wallet operations
- Emergency pause events
- Unusual transaction patterns

### 5. Audit Compliance

- Maintain audit logs for at least 7 years
- Regular security audits
- Penetration testing
- Compliance with AP2 mandates

---

## Security Checklist

### Pre-Production

- [ ] Generate and securely store encryption key
- [ ] Configure TLS certificates
- [ ] Set up KMS integration (recommended)
- [ ] Create admin agent account
- [ ] Configure multi-signature thresholds
- [ ] Configure time lock settings
- [ ] Set up monitoring and alerting
- [ ] Review and test emergency pause procedure

### Production

- [ ] All API endpoints use HTTPS
- [ ] Database connections use SSL
- [ ] Encryption key stored in KMS
- [ ] Regular key rotation schedule
- [ ] Audit logs enabled and monitored
- [ ] Backup and disaster recovery tested
- [ ] Security incident response plan documented

---

## Troubleshooting

### Authentication Issues

**Problem**: "Invalid authentication credentials"

**Solutions**:
- Verify API key is correct
- Check token hasn't expired (60 minutes)
- Ensure agent account is active
- Verify role has required permissions

### Encryption Issues

**Problem**: "Failed to decrypt data"

**Solutions**:
- Verify ENCRYPTION_KEY matches the key used to encrypt
- Check key hasn't been rotated without re-encrypting data
- Ensure key is properly base64-encoded

### TLS Issues

**Problem**: "SSL certificate verification failed"

**Solutions**:
- Verify certificate is valid and not expired
- Check certificate chain is complete
- Ensure certificate matches domain name
- Verify TLS 1.3 is supported by client

### Wallet Security Issues

**Problem**: "Wallet is paused"

**Solutions**:
- Check pause reason in security config
- Contact Escrow Agent to resume wallet
- Review audit trail for security incidents

---

## Support

For security-related questions or to report vulnerabilities:

- Email: security@example.com
- Emergency: +1-XXX-XXX-XXXX
- Bug Bounty: https://example.com/security/bounty

**Do not** disclose security vulnerabilities publicly.
