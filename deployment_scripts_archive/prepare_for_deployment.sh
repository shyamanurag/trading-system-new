#!/bin/bash

echo "🚀 Preparing for deployment..."

# Create frontend environment file
echo "📝 Creating frontend .env.production..."
cat > src/frontend/.env.production << EOF
VITE_API_URL=https://algoauto-ua2iq.ondigitalocean.app
EOF

# Update health check to not use localhost
echo "🔧 Fixing health check..."
sed -i 's/localhost:${port}/0.0.0.0:${port}/g' health_check.py 2>/dev/null || \
sed -i '' 's/localhost:${port}/0.0.0.0:${port}/g' health_check.py

# Ensure JWT_SECRET is set
echo "🔐 Checking JWT_SECRET..."
if ! grep -q "JWT_SECRET" .env.local 2>/dev/null; then
    echo "JWT_SECRET=your-secret-key-here-change-in-production" >> .env.local
fi

# Update package.json build command
echo "📦 Updating package.json..."
cd src/frontend
npm pkg set scripts.build="vite build --mode production"
cd ../..

# Create a deployment checklist
echo "📋 Creating deployment checklist..."
cat > DEPLOYMENT_CHECKLIST.md << 'EOF'
# Deployment Checklist

## Pre-deployment
- [ ] All tests passing
- [ ] Environment variables set in DigitalOcean
- [ ] JWT_SECRET changed from default
- [ ] Database migrations run
- [ ] Redis connection configured

## Frontend
- [ ] VITE_API_URL set to production URL
- [ ] Build successful
- [ ] No console errors

## Backend
- [ ] Health check endpoint working
- [ ] Authentication working
- [ ] CORS configured for production domain
- [ ] Error handling in place

## Post-deployment
- [ ] Health check passing
- [ ] Can login with credentials
- [ ] WebSocket connections working
- [ ] No errors in logs
EOF

echo "✅ Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Review changes"
echo "2. Commit: git add -A && git commit -m 'Fix deployment issues'"
echo "3. Push: git push origin main"
echo "4. Deploy will start automatically on DigitalOcean" 