# 步数自动提交系统

一个基于 Flask 的自动化步数提交系统，支持多账号管理、定时任务和提交记录。

## 功能特性

- ✅ **多账号管理**：支持添加、编辑、删除多个账号
- ⏰ **定时任务**：每个账号可独立设置提交时间（北京时间）
- 📊 **提交记录**：详细记录每次提交的结果
- 📝 **系统日志**：记录系统运行状态和错误信息
- 🎨 **Web 界面**：美观的 Bootstrap 5 界面
- 🚀 **易于部署**：支持 Render 等平台一键部署

## 技术栈

- Python 3.11+
- Flask 3.0
- Flask-SQLAlchemy
- APScheduler（定时任务）
- Bootstrap 5

## 快速开始

### 本地运行

1. 克隆仓库
```bash
git clone <your-repo-url>
cd step_automation
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行应用
```bash
python app.py
```

5. 访问 http://localhost:5000

### 部署到 Render

1. Fork 或上传代码到 GitHub
2. 登录 [Render](https://render.com)
3. 点击 "New +" -> "Web Service"
4. 选择你的 GitHub 仓库
5. 配置：
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4`
6. 点击 "Create Web Service"

或使用 `render.yaml` 文件自动配置：
1. 在 Render Dashboard 中选择 "Blueprint"
2. 连接你的 GitHub 仓库
3. Render 会自动读取 `render.yaml` 配置

## 默认账号

系统初始化时会自动创建默认账号：
- 账号：`Tbh2356@163.com`
- 密码：`112233qq`
- 步数：`89888`
- 定时：`00:05`（每天凌晨 0 点 5 分）

## 使用说明

### 添加账号

1. 访问 "账号管理" 页面
2. 点击 "添加账号" 按钮
3. 填写账号信息：
   - 账号：邮箱或手机号
   - 密码：登录密码
   - 目标步数：建议 10000-100000
   - 定时时间：北京时间，格式为 时:分
4. 点击 "添加"

### 设置定时任务

每个账号可以独立设置定时时间：
- 小时：0-23
- 分钟：0-59

例如：
- `0:5` = 每天凌晨 0 点 5 分
- `8:0` = 每天早上 8 点整
- `23:30` = 每天晚上 11 点 30 分

### 手动提交

在账号列表中点击 "立即提交" 按钮可手动触发步数提交。

### 查看记录

- **提交记录**：查看每次提交的详细结果
- **系统日志**：查看系统运行状态和错误信息

## API 接口

### 账号管理

- `GET /api/accounts` - 获取所有账号
- `POST /api/accounts` - 创建账号
- `PUT /api/accounts/<id>` - 更新账号
- `DELETE /api/accounts/<id>` - 删除账号
- `POST /api/accounts/<id>/submit` - 手动提交步数

### 记录查询

- `GET /api/records` - 获取提交记录
- `GET /api/logs` - 获取系统日志
- `GET /api/stats` - 获取统计信息

## 注意事项

1. **频率限制**：目标 API 有频率限制，短时间内多次提交可能会失败
2. **Token 有效期**：Authorization 和 Time Token 可能有有效期，如遇到 "请求失败，请刷新页面重试" 错误，需要从浏览器抓包获取新的 Token
3. **时区**：所有定时任务使用北京时间（Asia/Shanghai）

## 更新 Token

如果提交失败并提示需要刷新页面，请：

1. 使用浏览器访问 http://8.140.250.130/bushu/
2. 登录账号并提交一次步数
3. 打开浏览器开发者工具（F12）
4. 在 Network 中找到 `step` 请求
5. 复制请求头中的 `Authorization` 和 `time` 值
6. 在账号编辑页面的 "高级设置" 中更新这两个值

## 项目结构

```
step_automation/
├── app.py                 # 主应用文件
├── requirements.txt       # Python 依赖
├── render.yaml           # Render 部署配置
├── Procfile              # 进程配置文件
├── README.md             # 项目说明
└── templates/            # HTML 模板
    ├── base.html         # 基础模板
    ├── index.html        # 首页
    ├── accounts.html     # 账号管理
    ├── records.html      # 提交记录
    └── logs.html         # 系统日志
```

## 许可证

MIT License
