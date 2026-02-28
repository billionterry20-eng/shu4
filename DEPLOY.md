# 部署指南

## Render 部署（推荐）

### 方法一：使用 Blueprint（推荐）

1. Fork 或上传代码到 GitHub/GitLab
2. 登录 [Render](https://render.com)
3. 点击 "New +" -> "Blueprint"
4. 选择你的代码仓库
5. Render 会自动读取 `render.yaml` 配置文件
6. 点击 "Apply" 完成部署

### 方法二：手动创建 Web Service

1. 登录 [Render](https://render.com)
2. 点击 "New +" -> "Web Service"
3. 选择你的代码仓库
4. 填写配置：
   - **Name**: `step-automation`（或你喜欢的名字）
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 4`
5. 点击 "Create Web Service"

### 环境变量配置

在 Render Dashboard 中设置以下环境变量：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | Flask 密钥（用于会话加密） | 自动生成 |
| `DATABASE_URL` | 数据库连接 URL | `sqlite:///step_automation.db` |

## 其他平台部署

### Heroku

1. 安装 Heroku CLI
2. 登录并创建应用：
```bash
heroku login
heroku create your-app-name
```

3. 部署：
```bash
git push heroku main
```

### PythonAnywhere

1. 上传代码到 PythonAnywhere
2. 创建虚拟环境并安装依赖
3. 配置 WSGI 文件指向 `wsgi.py`
4. 设置每日任务（Scheduled Task）来执行定时任务

### 自建服务器

1. 克隆代码
```bash
git clone <your-repo-url>
cd step_automation
```

2. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 使用 Gunicorn 运行
```bash
gunicorn wsgi:application --bind 0.0.0.0:8000 --workers 1 --threads 4
```

5. 使用 Nginx 反向代理（生产环境推荐）

## 验证部署

部署完成后，访问你的应用 URL：

1. 首页应显示统计信息
2. 默认账号 `Tbh2356@163.com` 已自动创建
3. 定时任务会在每天 00:05（北京时间）自动执行

## 故障排查

### 应用无法启动

1. 检查日志：`render logs` 或平台提供的日志查看功能
2. 确认依赖安装成功：`pip install -r requirements.txt`
3. 检查端口配置：确保使用 `$PORT` 环境变量

### 定时任务不执行

1. 检查系统日志页面是否有错误信息
2. 确认账号已启用
3. 手动测试提交功能是否正常

### API 提交失败

1. 检查 Token 是否过期
2. 查看提交记录页面的错误信息
3. 可能需要从浏览器抓包获取新的 Token

## 更新 Token

如果提交失败并提示 "请求失败，请刷新页面重试"：

1. 使用浏览器访问 http://8.140.250.130/bushu/
2. 登录并手动提交一次步数
3. 打开开发者工具（F12）-> Network
4. 找到 `step` 请求，复制 `Authorization` 和 `time`
5. 在账号编辑页面的 "高级设置" 中更新
