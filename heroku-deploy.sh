#!/bin/bash
# Quick Heroku Deployment Script for NetWatch
# Run this after installing Heroku CLI and logging in

set -e

echo "=========================================="
echo "NetWatch - Heroku Quick Deploy"
echo "=========================================="
echo ""

# Check if app name provided
if [ -z "$1" ]; then
    echo "Usage: ./heroku-deploy.sh my-app-name"
    echo "Example: ./heroku-deploy.sh netwatch-monitor"
    exit 1
fi

APP_NAME=$1

echo "Step 1: Creating Heroku app '$APP_NAME'..."
heroku create $APP_NAME || echo "App may already exist"

echo ""
echo "Step 2: Adding PostgreSQL..."
heroku addons:create heroku-postgresql:mini --app=$APP_NAME || echo "PostgreSQL may already be added"

echo ""
echo "Step 3: Adding Redis..."
heroku addons:create heroku-redis:mini --app=$APP_NAME || echo "Redis may already be added"

echo ""
echo "Step 4: Setting environment variables..."
read -p "Enter DJANGO_SECRET_KEY (generate with: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\"): " SECRET_KEY
read -p "Enter EMAIL_HOST_USER (Gmail address): " EMAIL_USER
read -p "Enter EMAIL_HOST_PASSWORD (Gmail app password): " EMAIL_PASS

heroku config:set \
    DEBUG=False \
    DJANGO_SECRET_KEY="$SECRET_KEY" \
    ALLOWED_HOSTS="$APP_NAME.herokuapp.com,www.$APP_NAME.herokuapp.com" \
    EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend \
    EMAIL_HOST=smtp.gmail.com \
    EMAIL_PORT=587 \
    EMAIL_USE_TLS=True \
    EMAIL_HOST_USER="$EMAIL_USER" \
    EMAIL_HOST_PASSWORD="$EMAIL_PASS" \
    DEFAULT_FROM_EMAIL="$EMAIL_USER" \
    ALERT_EMAIL_RECIPIENTS="$EMAIL_USER" \
    --app=$APP_NAME

echo ""
echo "Step 5: Pushing code to Heroku..."
git push heroku main || git push heroku master

echo ""
echo "Step 6: Running migrations..."
heroku run python manage.py migrate --app=$APP_NAME

echo ""
echo "Step 7: Creating superuser..."
heroku run python manage.py createsuperuser --app=$APP_NAME

echo ""
echo "Step 8: Scaling dynos..."
echo "Note: Free tier gets 1 free dyno. Choose web OR worker+beat"
read -p "Scale to: (web=1 worker=0 beat=0) for web only, or (web=0 worker=1 beat=1) for workers only? Enter 'web' or 'worker': " DYNO_TYPE

if [ "$DYNO_TYPE" = "web" ]; then
    heroku ps:scale web=1 worker=0 beat=0 --app=$APP_NAME
else
    heroku ps:scale web=0 worker=1 beat=1 --app=$APP_NAME
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "App URL: https://$APP_NAME.herokuapp.com"
echo "Admin URL: https://$APP_NAME.herokuapp.com/admin"
echo ""
echo "View logs:"
echo "  heroku logs --tail --app=$APP_NAME"
echo ""
echo "Scale dynos:"
echo "  heroku ps:scale web=1 worker=1 beat=1 --app=$APP_NAME"
echo ""
echo "View config:"
echo "  heroku config --app=$APP_NAME"
