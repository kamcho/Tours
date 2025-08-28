# 🗄️ Database Configuration Setup

## Overview
This project now automatically switches between different database configurations based on the environment:
- **Local Development**: Uses SQLite database
- **PythonAnywhere Production**: Uses MySQL database

## 🔧 How It Works

### Automatic Detection
The system detects the environment using the `PYTHONANYWHERE_SITE` environment variable:
- If running on PythonAnywhere → Uses MySQL
- If running locally → Uses SQLite

### Configuration Files
- **`travelske/settings.py`**: Contains the conditional database configuration
- **No additional files needed**: Everything is handled automatically

## 🚀 Local Development

### What Happens
- Database automatically switches to SQLite
- All migrations run against local SQLite database
- Development mode is enabled (DEBUG=True)
- Console email backend for testing

### Commands
```bash
# Check database configuration
python manage.py check

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver

# Create superuser
python manage.py createsuperuser
```

## 🌐 PythonAnywhere Production

### What Happens
- Database automatically switches to MySQL
- Production mode is enabled (DEBUG=False)
- Security headers are enabled
- Static files served from PythonAnywhere

### Database Details
- **Host**: `kevin254.mysql.pythonanywhere-services.com`
- **Database**: `kevin254$tours`
- **User**: `kevin254`
- **Password**: `141778215aA!@#`

## 📁 File Structure
```
travelske/
├── settings.py          # Main settings with conditional DB config
├── db.sqlite3          # Local SQLite database (auto-created)
└── migrations/         # Database migrations
```

## 🔒 Security Notes

### Local Development
- SQLite database is stored locally
- No external connections
- Safe for development

### Production
- MySQL credentials are in settings.py
- Database is only accessible from PythonAnywhere
- External connections are blocked for security

## 🚨 Troubleshooting

### Local Issues
1. **Port already in use**: Kill existing Django server
2. **Migration errors**: Delete `db.sqlite3` and run `migrate` again
3. **Import errors**: Ensure all dependencies are installed

### PythonAnywhere Issues
1. **Database connection failed**: Check credentials in settings.py
2. **Migration errors**: Ensure MySQL database exists and is accessible
3. **Static files not loading**: Check STATIC_ROOT path

## 📝 Environment Variables

The system automatically detects the environment, but you can override if needed:

```bash
# Force PythonAnywhere mode locally (for testing)
export PYTHONANYWHERE_SITE=test

# Force local mode on PythonAnywhere (not recommended)
unset PYTHONANYWHERE_SITE
```

## ✅ Verification

### Check Current Database
```bash
python manage.py check
```

You should see:
- **Local**: `💻 Using local SQLite database` + `🛠️ Development mode enabled`
- **PythonAnywhere**: `🚀 Using PythonAnywhere MySQL database` + `🔒 Production mode enabled`

### Test Database Connection
```bash
# Test database connectivity
python manage.py showmigrations

# Test server startup
python manage.py runserver --noreload
```

## 🎯 Benefits

1. **Zero Configuration**: Works automatically in both environments
2. **Secure**: No database credentials in code when developing locally
3. **Fast Development**: SQLite is fast for local development
4. **Production Ready**: MySQL for production performance and reliability
5. **Easy Deployment**: Just upload code to PythonAnywhere

## 🔄 Migration Process

### Local → Production
1. Develop locally with SQLite
2. Test everything works
3. Upload code to PythonAnywhere
4. System automatically switches to MySQL
5. Run migrations on PythonAnywhere if needed

### Production → Local
1. Download code from PythonAnywhere
2. System automatically switches to SQLite
3. Run migrations locally if needed
4. Continue development

---

**Note**: This setup ensures you can develop locally without any external database dependencies while maintaining full production functionality on PythonAnywhere.
