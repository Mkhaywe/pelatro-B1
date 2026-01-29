#!/usr/bin/env python
"""
Setup PostgreSQL database and create comprehensive demo data
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

def check_postgres_running():
    """Check if PostgreSQL is running"""
    try:
        import psycopg2
    except ImportError:
        return None, None, None  # psycopg2 not installed
    
    try:
        # Try to connect to default postgres database
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='postgres',
            user='postgres',
            password='postgres'
        )
        conn.close()
        return True, 'postgres', 'postgres'
    except psycopg2.OperationalError as e:
        # Try common default passwords
        for password in ['postgres', 'admin', '']:
            try:
                conn = psycopg2.connect(
                    host='localhost',
                    port=5432,
                    database='postgres',
                    user='postgres',
                    password=password
                )
                conn.close()
                return True, 'postgres', password
            except:
                continue
        return False, None, None
    except Exception as e:
        print(f"  [WARN] Could not connect to PostgreSQL: {e}")
        return False, None, None

def create_database(admin_user, admin_password, db_name, db_user, db_password):
    """Create database and user"""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Connect as admin
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='postgres',
            user=admin_user,
            password=admin_password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"  [OK] Created database: {db_name}")
        else:
            print(f"  [OK] Database {db_name} already exists")
        
        # Create user if not exists
        cursor.execute(f"SELECT 1 FROM pg_user WHERE usename = '{db_user}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE USER {db_user} WITH PASSWORD '{db_password}'")
            print(f"  [OK] Created user: {db_user}")
        else:
            print(f"  [OK] User {db_user} already exists")
            # Update password
            cursor.execute(f"ALTER USER {db_user} WITH PASSWORD '{db_password}'")
            print(f"  [OK] Updated password for {db_user}")
        
        # Grant privileges
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user}")
        print(f"  [OK] Granted privileges")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to create database: {e}")
        return False

def update_env_file(db_name, db_user, db_password):
    """Update .env file with PostgreSQL settings"""
    env_path = BASE_DIR / '.env'
    
    # Read existing .env
    env_vars = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Update database settings
    env_vars['USE_POSTGRES'] = 'True'
    env_vars['DB_NAME'] = db_name
    env_vars['DB_USER'] = db_user
    env_vars['DB_PASSWORD'] = db_password
    env_vars['DB_HOST'] = 'localhost'
    env_vars['DB_PORT'] = '5432'
    
    # Write back
    with open(env_path, 'w') as f:
        f.write("# Django Settings\n")
        f.write("SECRET_KEY=django-insecure-change-this-in-production\n")
        f.write("DEBUG=True\n\n")
        f.write("# Database Configuration\n")
        f.write(f"USE_POSTGRES={env_vars.get('USE_POSTGRES', 'True')}\n")
        f.write(f"DB_NAME={db_name}\n")
        f.write(f"DB_USER={db_user}\n")
        f.write(f"DB_PASSWORD={db_password}\n")
        f.write(f"DB_HOST={env_vars.get('DB_HOST', 'localhost')}\n")
        f.write(f"DB_PORT={env_vars.get('DB_PORT', '5432')}\n\n")
        
        # Write Xiva settings
        f.write("# Xiva BSS API Configuration\n")
        for key in ['XIVA_API_BASE_URL', 'XIVA_API_AUTH_TYPE', 'XIVA_API_USERNAME', 'XIVA_API_PASSWORD', 'XIVA_API_TIMEOUT']:
            if key in env_vars:
                f.write(f"{key}={env_vars[key]}\n")
        
        # Write other settings
        f.write("\n# DWH Configuration (Optional)\n")
        f.write("DWH_TYPE=postgresql\n\n")
        f.write("# Redis Configuration (Optional)\n")
        f.write("REDIS_HOST=localhost\n")
        f.write("REDIS_PORT=6379\n\n")
        f.write("# ML Configuration\n")
        f.write("ML_MOCK_MODE=True\n\n")
        f.write("# Kafka Configuration (Optional)\n")
        f.write("LOYALTY_KAFKA_ENABLED=False\n")
    
    print(f"  [OK] Updated .env file")

def main():
    print("\n" + "="*80)
    print("  POSTGRESQL SETUP AND DEMO DATA CREATION")
    print("="*80)
    
    # Step 1: Check PostgreSQL
    print("\n[1] Checking PostgreSQL...")
    result = check_postgres_running()
    
    if result[0] is None:
        print("  [ERROR] psycopg2-binary not installed in current Python environment")
        print("  [INFO] Installing psycopg2-binary...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary'], check=False)
        result = check_postgres_running()
    
    if not result[0]:
        print("  [ERROR] PostgreSQL is not running or not accessible")
        print("\n  Please:")
        print("    1. Install PostgreSQL from https://www.postgresql.org/download/")
        print("    2. Start PostgreSQL service")
        print("    3. Default credentials: user='postgres', password='postgres'")
        print("\n  Or run this script again after starting PostgreSQL")
        return False
    
    admin_user, admin_password = result[1], result[2]
    print(f"  [OK] PostgreSQL is running")
    
    # Step 2: Create database
    print("\n[2] Creating database and user...")
    db_name = 'loyalty_db'
    db_user = 'loyalty_user'
    db_password = 'loyalty_password'
    
    if not create_database(admin_user, admin_password, db_name, db_user, db_password):
        return False
    
    # Step 3: Update .env
    print("\n[3] Updating .env file...")
    update_env_file(db_name, db_user, db_password)
    
    # Step 4: Run migrations
    print("\n[4] Running database migrations...")
    try:
        result = subprocess.run(
            [sys.executable, 'manage.py', 'migrate'],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("  [OK] Migrations completed")
        else:
            print(f"  [ERROR] Migration failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  [ERROR] Failed to run migrations: {e}")
        return False
    
    # Step 5: Create superuser
    print("\n[5] Creating/updating superuser...")
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
        import django
        django.setup()
        
        from django.contrib.auth.models import User
        username = 'admin'
        password = 'admin123'
        
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            print(f"  [OK] Updated user: {username}")
        else:
            User.objects.create_superuser(username=username, email='admin@example.com', password=password)
            print(f"  [OK] Created user: {username}")
        
        print(f"  [INFO] Login: {username} / {password}")
    except Exception as e:
        print(f"  [WARN] Could not create user: {e}")
    
    # Step 6: Create demo data
    print("\n[6] Creating demo data...")
    print("  [INFO] Running create_full_demo.py...")
    try:
        result = subprocess.run(
            [sys.executable, 'create_full_demo.py'],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"  [ERROR] Demo creation had issues: {result.stderr}")
    except Exception as e:
        print(f"  [ERROR] Failed to create demo data: {e}")
    
    print("\n" + "="*80)
    print("  SETUP COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("  1. Restart Django server to use PostgreSQL")
    print("  2. Login with: admin / admin123")
    print("  3. View demo data in the frontend")
    print()
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

