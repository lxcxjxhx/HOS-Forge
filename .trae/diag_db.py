"""Diagnostic script for SQLite database path issues."""
import os
import sys
import traceback

os.environ['INSTALL_DOCKER'] = '0'
os.environ['RUNTIME'] = 'local'

print('=' * 70)
print('SQLite Path Diagnostic')
print('=' * 70)

# Step 1: Check what persistence_dir is configured
print('\n[Step 1] Getting global config and persistence_dir...')
try:
    from openhands.app_server.config import get_global_config
    global_config = get_global_config()
    db_session = global_config.db_session

    print(f'  persistence_dir (raw):    {db_session.persistence_dir!r}')
    print(f'  persistence_dir (type):   {type(db_session.persistence_dir).__name__}')
    print(f'  persistence_dir (abs):    {db_session.persistence_dir.absolute()!r}')
    print(f'  persistence_dir (exists): {db_session.persistence_dir.exists()}')
    print(f'  persistence_dir (is_dir): {db_session.persistence_dir.is_dir()}')

    # Check parent
    parent = db_session.persistence_dir.parent
    print(f'  parent dir:               {parent!r}')
    print(f'  parent exists:            {parent.exists()}')
    print(f'  parent writable:          {os.access(parent, os.W_OK) if parent.exists() else "N/A"}')
except Exception as e:
    print(f'  ERROR getting config: {type(e).__name__}: {e}')
    traceback.print_exc()
    sys.exit(1)

# Step 2: Force-create the directory
print('\n[Step 2] Force-creating persistence_dir...')
try:
    db_session.persistence_dir.mkdir(parents=True, exist_ok=True)
    print(f'  After mkdir, exists: {db_session.persistence_dir.exists()}')
    print(f'  After mkdir, is_dir: {db_session.persistence_dir.is_dir()}')
    # Try writing a test file
    test_file = db_session.persistence_dir / '_write_test.tmp'
    try:
        test_file.write_text('test')
        test_file.unlink()
        print('  Directory is writable: True')
    except Exception as e:
        print(f'  Directory is writable: False ({e})')
except Exception as e:
    print(f'  ERROR creating dir: {type(e).__name__}: {e}')
    traceback.print_exc()

# Step 3: Build URL and test engine
print('\n[Step 3] Building SQLite URL and creating engine...')
try:
    engine = db_session.get_db_engine()
    print(f'  Engine created: {engine!r}')
    print(f'  Engine URL:     {engine.url}')
except Exception as e:
    print(f'  ERROR creating engine: {type(e).__name__}: {e}')
    traceback.print_exc()
    sys.exit(1)

# Step 4: Test actual connection
print('\n[Step 4] Testing actual database connection...')
try:
    with engine.connect() as conn:
        result = conn.execute(__import__('sqlalchemy').text('SELECT 1'))
        print(f'  Connection successful. Result: {result.fetchone()}')
except Exception as e:
    print(f'  ERROR connecting: {type(e).__name__}: {e}')
    traceback.print_exc()

# Step 5: Try running alembic programmatically
print('\n[Step 5] Testing alembic migration path...')
try:
    # Replicate what alembic/env.py does
    from openhands.app_server.app_lifespan.alembic.env import run_migrations_online
    print('  Calling run_migrations_online()...')
    run_migrations_online()
    print('  Alembic migrations completed successfully!')
except Exception as e:
    print(f'  ERROR in alembic: {type(e).__name__}: {e}')
    traceback.print_exc()

print('\n' + '=' * 70)
print('Diagnostic complete.')
print('=' * 70)
