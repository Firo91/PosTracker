# Deploying NetWatch to Heroku

This guide walks you through deploying NetWatch to Heroku with PostgreSQL, Redis, and Celery workers.

## Prerequisites

1. **Heroku Account** - Sign up at https://www.heroku.com
2. **Heroku CLI** - Download from https://devcenter.heroku.com/articles/heroku-cli
3. **Git** - Version control (already in use)

## Step 1: Install Heroku CLI and Login

```powershell
# Login to Heroku
heroku login
```

## Step 2: Create Heroku App

```powershell
# Create app (choose unique name)
heroku create your-app-name

# Or add to existing remote if deploying existing app
heroku create

# Verify remote was added
git remote -v
```

## Step 3: Add Add-ons (PostgreSQL and Redis)

```powershell
# PostgreSQL database (free tier available)
heroku addons:create heroku-postgresql:mini

# Redis for Celery (free tier available)
heroku addons:create heroku-redis:mini

# Verify add-ons
heroku addons
```

## Step 4: Configure Environment Variables

```powershell
# Generate a secure secret key (run this locally in Python)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Set environment variables
heroku config:set DEBUG=False
heroku config:set DJANGO_SECRET_KEY=your-secret-key-from-above
heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com

# Email configuration (example with Gmail)
heroku config:set EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
heroku config:set EMAIL_HOST=smtp.gmail.com
heroku config:set EMAIL_PORT=587
heroku config:set EMAIL_USE_TLS=True
heroku config:set EMAIL_HOST_USER=your-email@gmail.com
heroku config:set EMAIL_HOST_PASSWORD=your-app-password
heroku config:set DEFAULT_FROM_EMAIL=netwatch@your-domain.com
heroku config:set ALERT_EMAIL_RECIPIENTS=admin@example.com

# Verify config
heroku config
```

**Note:** For Gmail:
- Use 2-factor authentication and generate an [App Password](https://support.google.com/accounts/answer/185833)
- Or use SendGrid: `heroku addons:create sendgrid:starter`

## Step 5: Update Database Environment Variable

Heroku's PostgreSQL add-on automatically sets `DATABASE_URL`. Update your settings to use it:

The app already reads from environment variables, but verify settings.py handles `DATABASE_URL`:

```python
# In settings.py, add this at the top if not present:
import dj-database-url
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

## Step 6: Update requirements.txt

Add these packages for Heroku:

```
dj-database-url==2.1.0
psycopg2-binary>=2.9.9
whitenoise>=6.6.0
gunicorn>=21.2.0
```

Or merge into existing requirements.txt

## Step 7: Deploy to Heroku

```powershell
# Push to Heroku (this triggers deployment)
git push heroku main

# Or if your main branch is named differently:
git push heroku your-branch-name:main
```

## Step 8: Run Database Migrations

```powershell
# Heroku runs the release phase (from Procfile) automatically
# Verify migrations ran:
heroku run python manage.py migrate

# Create superuser (optional, for admin access)
heroku run python manage.py createsuperuser
```

## Step 9: View Logs

```powershell
# Real-time logs
heroku logs --tail

# Web logs only
heroku logs --source app --tail

# Worker logs
heroku logs --source worker --tail
```

## Step 10: Scale Dynos (if needed)

```powershell
# View current dynos
heroku ps

# Scale web server (production: 2+ recommended)
heroku ps:scale web=1 worker=1 beat=1

# For free tier, only one free dyno allowed
# Scale to 0 to stop, 1 to run
heroku ps:scale web=1 worker=0 beat=0
```

---

## Heroku Dyno Types

| Type | Cost | Use Case |
|------|------|----------|
| Free | $0 | Hobby/testing (goes to sleep after 30 min inactivity) |
| Eco | $5/month | Lightweight, always-on |
| Basic | $12/month | 1GB RAM, reliable |
| Standard | $50/month | 2.5GB RAM, more power |

## Free Tier Limitations

⚠️ **Important for Free Tier:**
- App sleeps after 30 minutes of inactivity
- No SSL, but Heroku provides `*.herokuapp.com` SSL
- Limited add-on quotas
- 1 free dyno (choose web OR worker+beat)

**Recommendation:** Use free tier for testing, then upgrade to Eco ($5/month) for 24/7 monitoring.

## Troubleshooting

### App crashes after push
```powershell
heroku logs --tail
# Check for migration errors, missing dependencies, etc.
```

### Database errors
```powershell
# Reset database (destroys data!)
heroku pg:reset DATABASE

# Re-run migrations
heroku run python manage.py migrate
```

### Celery not running
```powershell
# Check if Redis is connected
heroku config:get REDIS_URL

# Scale worker/beat dynos
heroku ps:scale worker=1 beat=1
```

### Static files not loading
```powershell
# Collect static files manually
heroku run python manage.py collectstatic --noinput

# Check WhiteNoise is in MIDDLEWARE
heroku config:get MIDDLEWARE
```

---

## Production Checklist

- [ ] DEBUG=False in config
- [ ] DJANGO_SECRET_KEY is strong and random
- [ ] ALLOWED_HOSTS configured correctly
- [ ] PostgreSQL add-on created
- [ ] Redis add-on created
- [ ] Email configured (SendGrid or SMTP)
- [ ] Database migrated
- [ ] Superuser created
- [ ] Celery worker scaled to 1+
- [ ] Monitor logs for errors

## Next Steps

- **Custom Domain**: `heroku domains:add your-domain.com`
- **SSL Certificate**: Included free for `*.herokuapp.com` or custom domains
- **Monitoring**: Set up Heroku Alerts
- **Backups**: `heroku pg:backups` for PostgreSQL

For more: https://devcenter.heroku.com/articles/getting-started-with-python
