# How to Retrieve Policy Group IDs from Locus Dashboard

## Quick Guide

Since **Policy Groups are connected to company wallets**, here's the easiest way to find them:

### Step-by-Step Instructions

1. **Log into Locus Dashboard**
   - Go to: https://app.paywithlocus.com
   - Log in with your credentials

2. **Navigate to Wallets**
   - Click on **"Wallets"** in the sidebar
   - You'll see all your wallets listed

3. **Find the Company Wallet**
   - Look for the wallet address you need:
     - **LandAmerica**: `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d`
     - **AmeriSpec**: `0xaf30e4EaB2B65be3F447Ebb94328d0288F495aE9`
     - **CoreLogic**: `0x1FfFEBF263c5B04Ce0d8e30D61bAEaec4E4c5574`
     - **Fannie Mae**: `0x434a64Ee154551c089b00EbaAb74d11BC58E17Ba`

4. **Click on the Wallet**
   - Click on the wallet address or wallet name
   - This opens the wallet details page

5. **View Associated Policy Groups**
   - On the wallet details page, look for **"Policy Groups"** or **"Associated Policies"** section
   - You should see the Policy Group connected to this wallet
   - The Policy Group ID will be displayed (format: `policy_xxxxx`)

6. **Copy the Policy Group ID**
   - Copy the Policy Group ID
   - Add it to your `.env` file

### Alternative: Via Policy Groups Section

1. Navigate to **"Policy Groups"** in the sidebar
2. Find the policy by name:
   - "LandAmerica Title Verification Policy"
   - "AmeriSpec Home Inspection Policy"
   - "CoreLogic Property Valuation Policy"
   - "Fannie Mae Loan Verification Policy"
3. Click on the policy
4. View the **Policy Group ID** on the details page
5. Verify the **Associated Wallet** matches the correct address

### Verification

After retrieving each Policy Group ID, verify:
- ✅ Policy Group name matches the service
- ✅ Associated wallet address matches the company wallet
- ✅ Budget matches expected value ($0.03, $0.012, $0.010, $0.019)

### Example

For **LandAmerica**:
- **Wallet**: `0xA5CFa3b2AD61fdFe55E51375187743AC8BF8Be6d`
- **Policy Group**: "LandAmerica Title Verification Policy"
- **Policy Group ID**: `policy_xxxxx` (copy this)
- **Add to .env**: `LOCUS_POLICY_TITLE_ID=policy_xxxxx`

Repeat for all 4 companies!
