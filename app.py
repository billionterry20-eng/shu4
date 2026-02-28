"""
步数自动提交系统
支持多账号管理、定时任务、提交记录
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
import pytz
import os
import json
import atexit

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///step_automation.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 北京时区
beijing_tz = pytz.timezone('Asia/Shanghai')

# API 配置
API_URL = "http://8.140.250.130/king/api/step"
DEFAULT_AUTH = "5aa77abb20f11a5e7f2440747a655a55"
DEFAULT_TIME = "1772274234275"


# ==================== 数据库模型 ====================

class Account(db.Model):
    """账号模型"""
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    steps = db.Column(db.Integer, default=89888)
    hour = db.Column(db.Integer, default=0)      # 定时小时 (0-23)
    minute = db.Column(db.Integer, default=5)    # 定时分钟 (0-59)
    enabled = db.Column(db.Boolean, default=True)
    auth_token = db.Column(db.String(64), default=DEFAULT_AUTH)
    time_token = db.Column(db.String(20), default=DEFAULT_TIME)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(beijing_tz))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(beijing_tz), onupdate=lambda: datetime.now(beijing_tz))
    
    # 关联提交记录
    records = db.relationship('SubmitRecord', backref='account', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Account {self.phone}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'password': '*' * len(self.password),
            'steps': self.steps,
            'hour': self.hour,
            'minute': self.minute,
            'enabled': self.enabled,
            'schedule': f"{self.hour:02d}:{self.minute:02d}",
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class SubmitRecord(db.Model):
    """提交记录模型"""
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    steps = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success / failed
    message = db.Column(db.String(500))
    response_code = db.Column(db.Integer)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(beijing_tz))
    
    def __repr__(self):
        return f'<SubmitRecord {self.id} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'account_phone': self.account.phone if self.account else 'Unknown',
            'steps': self.steps,
            'status': self.status,
            'message': self.message,
            'response_code': self.response_code,
            'submitted_at': self.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if self.submitted_at else None
        }


class SystemLog(db.Model):
    """系统日志模型"""
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), default='INFO')  # INFO / WARNING / ERROR
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(beijing_tz))
    
    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'message': self.message,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


# ==================== 核心功能 ====================

def add_system_log(message, level='INFO'):
    """添加系统日志"""
    try:
        log = SystemLog(level=level, message=message)
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"添加日志失败: {e}")
        db.session.rollback()


def submit_steps(account):
    """
    提交步数
    :param account: Account 对象
    :return: (success: bool, message: str, response_code: int)
    """
    headers = {
        "Host": "8.140.250.130",
        "Accept": "*/*",
        "Authorization": account.auth_token or DEFAULT_AUTH,
        "X-Requested-With": "XMLHttpRequest",
        "time": account.time_token or DEFAULT_TIME,
        "Accept-Language": "zh-TW,zh-Hant;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "http://8.140.250.130",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
        "Referer": "http://8.140.250.130/bushu/",
        "Connection": "keep-alive"
    }
    
    data = {
        "phone": account.phone,
        "pwd": account.password,
        "num": str(account.steps)
    }
    
    try:
        response = requests.post(API_URL, headers=headers, data=data, timeout=30)
        result = response.json()
        
        success = result.get('code') == 200 and result.get('msg') == 'success'
        message = result.get('data') or result.get('msg', 'Unknown response')
        response_code = result.get('code', 0)
        
        return success, message, response_code
        
    except requests.exceptions.RequestException as e:
        return False, f"网络请求错误: {str(e)}", 0
    except json.JSONDecodeError as e:
        return False, f"解析响应失败: {str(e)}", 0
    except Exception as e:
        return False, f"未知错误: {str(e)}", 0


def record_submission(account, success, message, response_code):
    """记录提交结果"""
    try:
        record = SubmitRecord(
            account_id=account.id,
            steps=account.steps,
            status='success' if success else 'failed',
            message=message,
            response_code=response_code
        )
        db.session.add(record)
        db.session.commit()
    except Exception as e:
        print(f"记录提交结果失败: {e}")
        db.session.rollback()


def execute_account_task(account_id):
    """执行单个账号的定时任务"""
    with app.app_context():
        account = Account.query.get(account_id)
        if not account:
            add_system_log(f"账号 ID {account_id} 不存在", 'ERROR')
            return
        
        if not account.enabled:
            add_system_log(f"账号 {account.phone} 已禁用，跳过执行", 'INFO')
            return
        
        add_system_log(f"开始执行账号 {account.phone} 的步数提交任务", 'INFO')
        
        success, message, response_code = submit_steps(account)
        record_submission(account, success, message, response_code)
        
        if success:
            add_system_log(f"账号 {account.phone} 步数提交成功: {account.steps} 步", 'INFO')
        else:
            add_system_log(f"账号 {account.phone} 步数提交失败: {message}", 'WARNING')


# ==================== 定时任务管理 ====================

scheduler = BackgroundScheduler(timezone=beijing_tz)


def init_scheduler():
    """初始化定时任务"""
    scheduler.start()
    load_all_jobs()
    add_system_log("定时任务调度器已启动", 'INFO')


def load_all_jobs():
    """加载所有账号的定时任务"""
    with app.app_context():
        accounts = Account.query.all()
        for account in accounts:
            schedule_account_job(account)


def schedule_account_job(account):
    """
    为单个账号设置定时任务
    每个账号使用独立的 job，确保互不干扰
    """
    job_id = f"account_job_{account.id}"
    
    # 如果任务已存在，先移除
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    if account.enabled:
        trigger = CronTrigger(hour=account.hour, minute=account.minute)
        scheduler.add_job(
            func=execute_account_task,
            trigger=trigger,
            id=job_id,
            args=[account.id],
            replace_existing=True,
            misfire_grace_time=3600  # 允许 1 小时的延迟执行
        )
        add_system_log(f"已为账号 {account.phone} 设置定时任务: 每天 {account.hour:02d}:{account.minute:02d}", 'INFO')


def remove_account_job(account_id):
    """移除账号的定时任务"""
    job_id = f"account_job_{account_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


# ==================== 路由 ====================

@app.route('/')
def index():
    """首页"""
    accounts = Account.query.all()
    recent_records = SubmitRecord.query.order_by(SubmitRecord.submitted_at.desc()).limit(10).all()
    
    # 统计信息
    total_accounts = len(accounts)
    enabled_accounts = sum(1 for a in accounts if a.enabled)
    today = datetime.now(beijing_tz).date()
    today_records = SubmitRecord.query.filter(
        db.func.date(SubmitRecord.submitted_at) == today
    ).all()
    today_success = sum(1 for r in today_records if r.status == 'success')
    
    return render_template('index.html', 
                          accounts=accounts, 
                          recent_records=recent_records,
                          total_accounts=total_accounts,
                          enabled_accounts=enabled_accounts,
                          today_submissions=len(today_records),
                          today_success=today_success)


@app.route('/accounts')
def accounts():
    """账号管理页面"""
    accounts = Account.query.all()
    return render_template('accounts.html', accounts=accounts)


@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """获取所有账号 API"""
    accounts = Account.query.all()
    return jsonify([account.to_dict() for account in accounts])


@app.route('/api/accounts', methods=['POST'])
def create_account():
    """创建账号 API"""
    data = request.get_json()
    
    # 验证必填字段
    if not data.get('phone') or not data.get('password'):
        return jsonify({'success': False, 'message': '账号和密码不能为空'}), 400
    
    # 创建账号
    account = Account(
        phone=data['phone'],
        password=data['password'],
        steps=data.get('steps', 89888),
        hour=data.get('hour', 0),
        minute=data.get('minute', 5),
        enabled=data.get('enabled', True),
        auth_token=data.get('auth_token', DEFAULT_AUTH),
        time_token=data.get('time_token', DEFAULT_TIME)
    )
    
    try:
        db.session.add(account)
        db.session.commit()
        
        # 设置定时任务
        schedule_account_job(account)
        
        add_system_log(f"创建账号成功: {account.phone}", 'INFO')
        return jsonify({'success': True, 'message': '账号创建成功', 'account': account.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'}), 500


@app.route('/api/accounts/<int:account_id>', methods=['PUT'])
def update_account(account_id):
    """更新账号 API"""
    account = Account.query.get_or_404(account_id)
    data = request.get_json()
    
    # 更新字段
    if 'phone' in data:
        account.phone = data['phone']
    if 'password' in data:
        account.password = data['password']
    if 'steps' in data:
        account.steps = data['steps']
    if 'hour' in data:
        account.hour = data['hour']
    if 'minute' in data:
        account.minute = data['minute']
    if 'enabled' in data:
        account.enabled = data['enabled']
    if 'auth_token' in data:
        account.auth_token = data['auth_token']
    if 'time_token' in data:
        account.time_token = data['time_token']
    
    try:
        db.session.commit()
        
        # 重新设置定时任务
        schedule_account_job(account)
        
        add_system_log(f"更新账号成功: {account.phone}", 'INFO')
        return jsonify({'success': True, 'message': '账号更新成功', 'account': account.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    """删除账号 API"""
    account = Account.query.get_or_404(account_id)
    
    try:
        # 移除定时任务
        remove_account_job(account_id)
        
        phone = account.phone
        db.session.delete(account)
        db.session.commit()
        
        add_system_log(f"删除账号成功: {phone}", 'INFO')
        return jsonify({'success': True, 'message': '账号删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@app.route('/api/accounts/<int:account_id>/submit', methods=['POST'])
def manual_submit(account_id):
    """手动提交步数 API"""
    account = Account.query.get_or_404(account_id)
    
    success, message, response_code = submit_steps(account)
    record_submission(account, success, message, response_code)
    
    if success:
        return jsonify({'success': True, 'message': f'提交成功: {account.steps} 步'})
    else:
        return jsonify({'success': False, 'message': f'提交失败: {message}'}), 400


@app.route('/records')
def records():
    """提交记录页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    pagination = SubmitRecord.query.order_by(SubmitRecord.submitted_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('records.html', pagination=pagination)


@app.route('/api/records', methods=['GET'])
def get_records():
    """获取提交记录 API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    account_id = request.args.get('account_id', type=int)
    
    query = SubmitRecord.query
    if account_id:
        query = query.filter_by(account_id=account_id)
    
    pagination = query.order_by(SubmitRecord.submitted_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'records': [record.to_dict() for record in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@app.route('/logs')
def logs():
    """系统日志页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    pagination = SystemLog.query.order_by(SystemLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('logs.html', pagination=pagination)


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """获取系统日志 API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    level = request.args.get('level')
    
    query = SystemLog.query
    if level:
        query = query.filter_by(level=level)
    
    pagination = query.order_by(SystemLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计信息 API"""
    total_accounts = Account.query.count()
    enabled_accounts = Account.query.filter_by(enabled=True).count()
    
    today = datetime.now(beijing_tz).date()
    today_records = SubmitRecord.query.filter(
        db.func.date(SubmitRecord.submitted_at) == today
    ).all()
    
    today_success = sum(1 for r in today_records if r.status == 'success')
    today_failed = len(today_records) - today_success
    
    # 最近7天的统计
    seven_days_ago = today - timedelta(days=7)
    recent_records = SubmitRecord.query.filter(
        db.func.date(SubmitRecord.submitted_at) >= seven_days_ago
    ).all()
    
    recent_success = sum(1 for r in recent_records if r.status == 'success')
    recent_failed = len(recent_records) - recent_success
    
    return jsonify({
        'accounts': {
            'total': total_accounts,
            'enabled': enabled_accounts,
            'disabled': total_accounts - enabled_accounts
        },
        'today': {
            'total': len(today_records),
            'success': today_success,
            'failed': today_failed
        },
        'recent_7days': {
            'total': len(recent_records),
            'success': recent_success,
            'failed': recent_failed
        }
    })


# ==================== 初始化 ====================

def init_default_account():
    """初始化默认账号"""
    with app.app_context():
        # 检查是否已有账号
        if Account.query.count() == 0:
            default_account = Account(
                phone="Tbh2356@163.com",
                password="112233qq",
                steps=89888,
                hour=0,
                minute=5,
                enabled=True,
                auth_token=DEFAULT_AUTH,
                time_token=DEFAULT_TIME
            )
            db.session.add(default_account)
            db.session.commit()
            print("已创建默认账号")


# 注册关闭钩子
atexit.register(lambda: scheduler.shutdown())

# ==================== 主程序 ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_default_account()
    
    init_scheduler()
    
    # 获取端口
    port = int(os.environ.get('PORT', 5000))
    
    app.run(host='0.0.0.0', port=port, debug=False)
