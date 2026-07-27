"""Temporary script to test server startup with custom persistence dir."""
import os
import traceback
from pathlib import Path

# Set persistence dir to a location allowed by Trae sandbox
project_root = Path(__file__).parent.parent
persistence_dir = project_root / '.trae' / 'workspace_persistence'
persistence_dir.mkdir(parents=True, exist_ok=True)

os.environ['INSTALL_DOCKER'] = '0'
os.environ['RUNTIME'] = 'local'
os.environ['OH_PERSISTENCE_DIR'] = str(persistence_dir)

print(f'Using persistence dir: {persistence_dir}')

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
