# 🚀 Deployment Guide - PadelTour API

This guide explains how to set up and use the CI/CD pipeline for automated deployments to Heroku.

## 🏗️ Pipeline Overview

Our CI/CD pipeline uses **GitHub Actions** and includes:

1. **Testing Stage**: Runs tests, linting, and migrations on every PR/push
2. **Deployment Stage**: Automatically deploys to Heroku on main branch pushes
3. **Verification**: Checks that the deployment was successful

## 📋 Prerequisites

- [x] Heroku account with the app already created (`api-tournme`)
- [x] GitHub repository connected to your project
- [x] Supabase database configured

## 🔧 Setup Instructions

### 1. Configure GitHub Secrets

You need to add these secrets to your GitHub repository:

Go to: **GitHub Repository → Settings → Secrets and variables → Actions**

Add the following secrets:

| Secret Name | Description | How to get it |
|-------------|-------------|---------------|
| `HEROKU_API_KEY` | Your Heroku API key | Go to [Heroku Account Settings](https://dashboard.heroku.com/account) → API Key |
| `HEROKU_EMAIL` | Your Heroku account email | The email you use to login to Heroku |

### 2. Get Your Heroku API Key

```bash
# Method 1: Via Heroku CLI
heroku auth:token

# Method 2: Via Heroku Dashboard
# Go to https://dashboard.heroku.com/account
# Scroll to "API Key" section
# Click "Reveal" and copy the key
```

### 3. Add Secrets to GitHub

1. Go to your repository on GitHub
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret:
   - Name: `HEROKU_API_KEY`, Value: `your_heroku_api_key`
   - Name: `HEROKU_EMAIL`, Value: `your_email@example.com`

## 🔄 How the Pipeline Works

### Automatic Triggers

The pipeline runs on:
- **Pull Requests**: Runs tests only (no deployment)
- **Push to main**: Runs tests + deployment

### Pipeline Stages

1. **Test Stage** (runs on all PRs and pushes):
   ```
   ✅ Setup Python 3.11
   ✅ Install dependencies
   ✅ Run database migrations
   ✅ Run tests
   ✅ Code linting (optional)
   ```

2. **Deploy Stage** (runs only on main branch pushes):
   ```
   ✅ Deploy to Heroku
   ✅ Run migrations on production
   ✅ Verify deployment
   ```

## 🚀 Deployment Process

### Manual Deployment (Current)
```bash
# 1. Make your changes
git add .
git commit -m "Your changes"

# 2. Push to main branch
git push origin main

# 3. The pipeline will automatically:
#    - Run tests
#    - Deploy to Heroku
#    - Run migrations
#    - Verify deployment
```

### Feature Branch Workflow (Recommended)
```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Make changes and commit
git add .
git commit -m "Add new feature"

# 3. Push feature branch
git push origin feature/new-feature

# 4. Create Pull Request on GitHub
#    - Tests will run automatically
#    - Review the PR
#    - Merge to main when ready

# 5. Automatic deployment happens when merged to main
```

## 🔍 Monitoring Deployments

### Check Pipeline Status
- Go to your GitHub repository → **Actions** tab
- See all workflow runs and their status

### Check Heroku Deployment
```bash
# View logs
heroku logs --tail --app api-tournme

# Check app status
heroku ps --app api-tournme

# Open the app
heroku open --app api-tournme
```

### Verify API Health
```bash
# Test API endpoint
curl https://api-tournme-22f05149d967.herokuapp.com/

# Check API docs
open https://api-tournme-22f05149d967.herokuapp.com/api/docs
```

## 🧪 Running Tests Locally

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html
```

## 🔧 Adding More Tests

Create test files in the `tests/` directory:

```python
# tests/test_your_feature.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_your_endpoint():
    response = client.get("/api/v1/your-endpoint")
    assert response.status_code == 200
```

## 🛠️ Troubleshooting

### Pipeline Fails
1. Check the **Actions** tab on GitHub for error details
2. Common issues:
   - Missing secrets
   - Test failures
   - Database connection issues

### Deployment Fails
1. Check Heroku logs: `heroku logs --tail --app api-tournme`
2. Verify environment variables: `heroku config --app api-tournme`
3. Manual deployment: `git push heroku main`

### Database Issues
```bash
# Run migrations manually
heroku run alembic upgrade head --app api-tournme

# Check database connection
heroku run python -c "from app.db.database import engine; print(engine.execute('SELECT 1').scalar())" --app api-tournme
```

## 📊 Pipeline Configuration

The pipeline is configured in `.github/workflows/deploy.yml` with:

- **Python 3.11**
- **PostgreSQL 13** for testing
- **Automatic caching** for faster builds
- **Environment variables** for testing
- **Heroku deployment** with verification

## 🎯 Next Steps

1. **Add more tests** as you develop new features
2. **Set up staging environment** for pre-production testing
3. **Add code coverage** reporting
4. **Implement database backups** before deployments
5. **Add Slack/email notifications** for deployment status

## 📚 Useful Commands

```bash
# Check pipeline status
gh run list  # Requires GitHub CLI

# Trigger manual deployment
git commit --allow-empty -m "Trigger deployment"
git push origin main

# Rollback deployment (if needed)
heroku releases:rollback --app api-tournme

# View environment variables
heroku config --app api-tournme
```

---

🎉 **Your CI/CD pipeline is ready!** Every push to main will automatically deploy your application to Heroku. 