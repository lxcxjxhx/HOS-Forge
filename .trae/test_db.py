#!/usr/bin/env python3
"""测试数据库连接"""
import os

print('=== 测试数据库连接 ===')

# 获取配置
from openhands.app_server.config import get_global_config  # noqa: E402

gc = get_global_config()
persistence_dir = gc.db_session.persistence_dir

print(f'persistence_dir: {persistence_dir}')
print(f'exists: {os.path.exists(persistence_dir)}')

# 创建目录
if not os.path.exists(persistence_dir):
    print(f'创建目录: {persistence_dir}')
    os.makedirs(persistence_dir, exist_ok=True)
    print(f'创建成功: {os.path.exists(persistence_dir)}')

# 测试数据库引擎
print('\n=== 测试数据库引擎 ===')
try:
    engine = gc.db_session.get_db_engine()
    print(f'引擎创建成功: {engine}')

    # 测试连接
    with engine.connect() as conn:
        print('数据库连接成功!')

except Exception as e:
    print(f'错误: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
