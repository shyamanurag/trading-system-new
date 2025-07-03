# Zerodha Kite Connect App Setup Guide

## Step 1: Create App on Kite Connect

1. Go to: https://developers.kite.trade/
2. Login with your Zerodha credentials
3. Click "Create new app"

## Step 2: Fill App Details

### App Information:
- **App name**: `AlgoAuto Trading System`
- **App type**: `Connect` (for trading apps)

### URLs Configuration:
- **Redirect URL**: 
  ```
  https://algoauto-9gx56.ondigitalocean.app/auth/zerodha/callback
  ```
  
  For local testing, you can add:
  ```
  http://localhost:8000/auth/zerodha/callback
  ```

- **Postback URL** (Optional for order updates):
  ```
  https://algoauto-9gx56.ondigitalocean.app/api/v1/webhooks/zerodha
  ```

### App Description:
```
Automated trading system with:
- Multiple trading strategies
- Risk management
- Real-time market analysis
- Position tracking
- Performance analytics
```

## Step 3: App Permissions

Select these permissions:
- ✅ **Profile** - Access user profile
- ✅ **Orders** - Place, modify, cancel orders
- ✅ **Holdings** - Access holdings
- ✅ **Positions** - Access positions
- ✅ **Funds** - Access funds and margins
- ✅ **Historical** - Access historical data (if needed)

## Step 4: Save Credentials

After creation, you'll get:
- **API Key**: `your_api_key_here`
- **API Secret**: `your_api_secret_here`

## Step 5: Update Your System

### Option A: Update Environment Variables
Add to your DigitalOcean App Platform environment:
```
ZERODHA_API_KEY=your_new_api_key
ZERODHA_API_SECRET=your_new_api_secret
```

### Option B: Update Config File
Update `config/production.env`:
```env
ZERODHA_API_KEY=your_new_api_key
ZERODHA_API_SECRET=your_new_api_secret
ZERODHA_USER_ID=your_user_id
```

## Step 6: Get Login URL

After updating credentials, get the authorization URL:
```
https://kite.zerodha.com/connect/login?api_key=your_new_api_key
```

## Step 7: Authentication Flow

1. Visit the authorization URL
2. Login with Zerodha credentials
3. You'll be redirected to:
   ```
   https://algoauto-9gx56.ondigitalocean.app/auth/zerodha/callback?request_token=xxxxx&action=login&status=success
   ```
4. Copy the `request_token` value
5. Use it at: https://algoauto-9gx56.ondigitalocean.app/auth/zerodha/

## Important Notes:

1. **Redirect URL Must Match**: The redirect URL in your app MUST exactly match what you configured
2. **HTTPS Required**: For production, use HTTPS URLs
3. **Token Expiry**: Request tokens expire in a few minutes
4. **Daily Login**: Zerodha requires daily authentication
5. **Rate Limits**: Be aware of API rate limits

## Troubleshooting:

### "Invalid API key" Error:
- Check if API key is correctly set in environment
- Ensure no extra spaces in the key

### "Token is invalid or expired" Error:
- Request tokens expire quickly (few minutes)
- Get a fresh token immediately after login

### "Invalid redirect URL" Error:
- Redirect URL must exactly match app configuration
- Check for trailing slashes or protocol differences

## Monthly Charges:

- Kite Connect has monthly charges (₹2000 + GST as of 2024)
- First month might be free for testing
- Check current pricing at: https://kite.trade/docs/connect/v3/

## Support:

- Kite Connect Forum: https://kite.trade/forum/
- API Documentation: https://kite.trade/docs/connect/v3/ 