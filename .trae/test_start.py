"""Temporary script to test server startup and capture errors."""
import os
import traceback
from pathlib import Path

# Use project-local persistence dir to avoid Trae Sandbox restrictions on ~\.openhands
_project_root = Path(__file__).resolve().parent.parent
_local_persistence = _project_root / '.trae' / 'workspace_persistence'
_local_persistence.mkdir(parents=True, exist_ok=True)

os.environ['INSTALL_DOCKER'] = '0'
os.environ['RUNTIME'] = 'local'
os.environ['OH_PERSISTENCE_DIR'] = str(_local_persistence)

print(f'Using persistence dir: {_local_persistence}')

try:
    print('[1/3] Importing uvicorn...')
    import uvicorn
    print('[2/3] Importing app from openhands.server.listen...')
    from openhands.server.listen import app
    print('[3/3] Import OK. Starting uvicorn on 0.0.0.0:3000...')
    uvicorn.run(app, host='0.0.0.0', port=3000, log_level='info')
except Exception as e:
    print(f'\n=== ERROR ===\n{type(e).__name__}: {e}')
    traceback.print_exc()
