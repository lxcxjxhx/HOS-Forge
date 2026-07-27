"""Check detailed permissions and test write scenarios."""
import os
import traceback
from pathlib import Path

os.environ['INSTALL_DOCKER'] = '0'
os.environ['RUNTIME'] = 'local'

out_file = Path(r'c:\1AAA-PROJECT\HOS\HOS-Forge\.trae\perm_check_output.txt')
lines = []

def log(msg):
    lines.append(msg)

try:
    log('=' * 70)
    log('Permission and Write Test')
    log('=' * 70)

    target_dir = Path(r'C:\Users\46119\.openhands')
    log(f'\nTarget dir: {target_dir}')
    log(f'  exists: {target_dir.exists()}')
    log(f'  is_dir: {target_dir.is_dir()}')

    # Check os.access
    log(f'  os.access(R_OK): {os.access(target_dir, os.R_OK)}')
    log(f'  os.access(W_OK): {os.access(target_dir, os.W_OK)}')
    log(f'  os.access(X_OK): {os.access(target_dir, os.X_OK)}')

    # Try different write methods
    log('\n[Write Test 1] Path.write_text()')
    try:
        test1 = target_dir / '_test1.tmp'
        test1.write_text('hello')
        log(f'  SUCCESS: wrote {test1}')
        test1.unlink()
        log('  Cleaned up')
    except Exception as e:
        log(f'  FAILED: {type(e).__name__}: {e}')

    log('\n[Write Test 2] open() with "w" mode')
    try:
        test2 = target_dir / '_test2.tmp'
        with open(test2, 'w', encoding='utf-8') as f:
            f.write('hello')
        log(f'  SUCCESS: wrote {test2}')
        os.remove(test2)
        log('  Cleaned up')
    except Exception as e:
        log(f'  FAILED: {type(e).__name__}: {e}')

    log('\n[Write Test 3] sqlite3 direct')
    try:
        import sqlite3
        db_path = target_dir / '_test3.db'
        log(f'  db_path: {db_path}')
        log(f'  db_path exists before: {db_path.exists()}')
        conn = sqlite3.connect(str(db_path))
        log('  Connection created')
        conn.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER)')
        conn.commit()
        log('  Table created and committed')
        conn.close()
        log('  Connection closed')
        log(f'  db_path exists after: {db_path.exists()}')
        if db_path.exists():
            db_path.unlink()
            log('  Cleaned up db')
        # Also clean journal files
        for suffix in ['-journal', '-wal', '-shm']:
            p = Path(str(db_path) + suffix)
            if p.exists():
                p.unlink()
                log(f'  Cleaned up {p}')
    except Exception as e:
        log(f'  FAILED: {type(e).__name__}: {e}')
        log(traceback.format_exc())

    # Check if openhands.db already exists
    db_file = target_dir / 'openhands.db'
    log('\n[Existing DB] openhands.db')
    log(f'  exists: {db_file.exists()}')
    if db_file.exists():
        log(f'  size: {db_file.stat().st_size}')
        log(f'  is_file: {db_file.is_file()}')
        try:
            # Try to open it
            import sqlite3
            conn = sqlite3.connect(str(db_file))
            conn.execute('SELECT 1')
            conn.close()
            log('  Can connect: True')
        except Exception as e:
            log(f'  Can connect: False ({e})')

    # Check current working directory
    log('\n[Environment]')
    log(f'  cwd: {os.getcwd()}')
    log(f'  HOME: {os.environ.get("HOME", "N/A")}')
    log(f'  USERPROFILE: {os.environ.get("USERPROFILE", "N/A")}')
    log(f'  Path.home(): {Path.home()}')

    # Try writing to cwd as fallback
    log('\n[Fallback Test] Write to cwd')
    try:
        test_cwd = Path.cwd() / '_test_cwd.db'
        import sqlite3
        conn = sqlite3.connect(str(test_cwd))
        conn.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER)')
        conn.commit()
        conn.close()
        log(f'  SUCCESS: wrote to {test_cwd}')
        test_cwd.unlink(missing_ok=True)
    except Exception as e:
        log(f'  FAILED: {type(e).__name__}: {e}')

    log('\n=== DONE ===')

except Exception as e:
    log(f'\n!!! FATAL: {type(e).__name__}: {e}')
    log(traceback.format_exc())

out_file.write_text('\n'.join(lines), encoding='utf-8')
print(f'Output written to {out_file}')
