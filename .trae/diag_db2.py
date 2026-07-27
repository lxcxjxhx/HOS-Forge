"""Diagnostic script - output to file to avoid log flooding."""
import os
import traceback
from pathlib import Path

os.environ['INSTALL_DOCKER'] = '0'
os.environ['RUNTIME'] = 'local'

out_file = Path(r'c:\1AAA-PROJECT\HOS\HOS-Forge\.trae\diag_output.txt')
lines = []

def log(msg):
    lines.append(msg)

try:
    log('=' * 70)
    log('SQLite Path Diagnostic')
    log('=' * 70)

    # Step 1: Check what persistence_dir is configured
    log('\n[Step 1] Getting global config and persistence_dir...')
    from openhands.app_server.config import get_global_config
    global_config = get_global_config()
    db_session = global_config.db_session

    log(f'  persistence_dir (raw):    {db_session.persistence_dir!r}')
    log(f'  persistence_dir (type):   {type(db_session.persistence_dir).__name__}')
    log(f'  persistence_dir (abs):    {db_session.persistence_dir.absolute()!r}')
    log(f'  persistence_dir (exists): {db_session.persistence_dir.exists()}')
    log(f'  persistence_dir (is_dir): {db_session.persistence_dir.is_dir()}')

    parent = db_session.persistence_dir.parent
    log(f'  parent dir:               {parent!r}')
    log(f'  parent exists:            {parent.exists()}')

    # Step 2: Force-create the directory
    log('\n[Step 2] Force-creating persistence_dir...')
    db_session.persistence_dir.mkdir(parents=True, exist_ok=True)
    log(f'  After mkdir, exists: {db_session.persistence_dir.exists()}')

    # Test write
    test_file = db_session.persistence_dir / '_write_test.tmp'
    try:
        test_file.write_text('test')
        test_file.unlink()
        log('  Directory is writable: True')
    except Exception as e:
        log(f'  Directory is writable: False ({e})')

    # Step 3: Build URL and test engine
    log('\n[Step 3] Building SQLite URL and creating engine...')
    engine = db_session.get_db_engine()
    log(f'  Engine URL:     {engine.url}')

    # Step 4: Test actual connection
    log('\n[Step 4] Testing actual database connection...')
    import sqlalchemy
    with engine.connect() as conn:
        result = conn.execute(sqlalchemy.text('SELECT 1'))
        log(f'  Connection successful. Result: {result.fetchone()}')

    # Step 5: Check alembic env.py path construction
    log('\n[Step 5] Checking alembic env.py path...')
    # Simulate what alembic/env.py does in run_migrations_online
    connectable = db_session.get_db_engine()
    log(f'  Engine from get_db_engine(): {connectable.url}')

    log('\n=== ALL CHECKS PASSED ===')

except Exception as e:
    log(f'\n!!! ERROR: {type(e).__name__}: {e}')
    log(traceback.format_exc())

out_file.write_text('\n'.join(lines), encoding='utf-8')
print(f'Diagnostic output written to {out_file}')
