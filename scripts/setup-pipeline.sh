#!/bin/bash

# 🚀 PadelTour API - CI/CD Pipeline Setup Script
# This script helps you set up GitHub Actions for automated deployment

echo "🚀 Setting up CI/CD Pipeline for PadelTour API"
echo "=============================================="
echo ""

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI is not installed. Please install it first:"
    echo "   brew install heroku/brew/heroku"
    echo "   or visit: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

echo "✅ Heroku CLI found"

# Check if user is logged in to Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "🔐 Please login to Heroku first:"
    heroku login
fi

# Get user email
HEROKU_EMAIL=$(heroku auth:whoami)
echo "📧 Heroku Email: $HEROKU_EMAIL"

# Get API key
echo "🔑 Getting your Heroku API key..."
HEROKU_API_KEY=$(heroku auth:token)

echo ""
echo "🎯 Setup Instructions:"
echo "======================"
echo ""
echo "1. Go to your GitHub repository: https://github.com/YOUR_USERNAME/YOUR_REPO"
echo "2. Click: Settings → Secrets and variables → Actions"
echo "3. Click: New repository secret"
echo "4. Add these two secrets:"
echo ""
echo "   📝 Secret 1:"
echo "   Name: HEROKU_API_KEY"
echo "   Value: $HEROKU_API_KEY"
echo ""
echo "   📝 Secret 2:"
echo "   Name: HEROKU_EMAIL"
echo "   Value: $HEROKU_EMAIL"
echo ""
echo "✨ Once you add these secrets, your CI/CD pipeline will be ready!"
echo ""
echo "🚀 Next steps:"
echo "   - Push to main branch to trigger deployment"
echo "   - Create Pull Requests to run tests"
echo "   - Check the Actions tab for pipeline status"
echo ""
echo "📚 For detailed instructions, see: DEPLOYMENT.md" 