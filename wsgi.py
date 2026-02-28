"""
WSGI 入口文件
用于 Gunicorn 等 WSGI 服务器
"""

import os
import sys

# 添加项目目录到路径
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 导入应用
from app import app, db, init_scheduler, init_default_account

# 初始化数据库和默认账号
with app.app_context():
    db.create_all()
    init_default_account()

# 初始化定时任务
init_scheduler()

# WSGI 应用对象
application = app
