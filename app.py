import os
import sys
import re
import json
import requests
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_from_directory
from jinja2 import ChoiceLoader, FileSystemLoader

app = Flask(__name__)

# DeepSeek配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = "your-API-Key"  # 替换为实际API Key

def get_base_path():
    """获取运行路径"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

base_path = get_base_path()
external_template_dir = os.path.join(base_path, 'html')  # 外部模板目录
default_template_dir = os.path.join(app.root_path, 'templates')  # 默认模板目录

# 配置支持多目录的模板加载器
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(external_template_dir),
    FileSystemLoader(default_template_dir)
])

# 初始化目录
mail_dir = os.path.join(get_base_path(), 'mail')
os.makedirs(mail_dir, exist_ok=True)

def sanitize_filename(filename):
    """清理危险字符"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def save_message(username, message):
    """保存消息到文件"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_username = sanitize_filename(username)[:20]  # 限制用户名长度
        filename = f"{timestamp}_{safe_username}.txt"
        filepath = os.path.join(mail_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Username: {safe_username}\n")
            f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Message:\n{message[:500]}\n")  # 限制消息长度
    except Exception as e:
        app.logger.error(f"保存失败: {str(e)}")

def call_deepseek_api(question):
    """调用DeepSeek API"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-reasoner",
        "messages": [{"role": "user", "content": question[:300]}]  # 限制问题长度
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"API调用失败: {str(e)}"

def get_file_list():
    """获取可下载文件列表"""
    config_path = os.path.join(get_base_path(), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        valid_files = []
        for item in config.get('downloads', []):
            file_path = os.path.join(get_base_path(), item['path'])
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                valid_files.append({
                    'name': item['name'],
                    'path': item['path'],
                    'size': size
                })
        return valid_files
    except Exception as e:
        app.logger.error(f"读取配置文件失败: {str(e)}")
        return []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 消息保存验证
        username = request.form.get('username', '').strip()
        message = request.form.get('message', '').strip()
        question = request.form.get('question', '').strip()

        # 处理消息保存
        if username and message:
            if len(username) > 20:
                return jsonify({'error': '用户名过长（最多20字符）'}), 400
            if len(message) > 500:
                return jsonify({'error': '消息过长（最多500字符）'}), 400
            save_message(username, message)
            return jsonify({'status': 'success'})

        # 处理问题咨询
        if question:
            if len(question) > 300:
                return jsonify({'error': '问题过长（最多300字符）'}), 400
            answer = call_deepseek_api(question)
            return jsonify({'answer': answer})

        return jsonify({'error': '无效请求'}), 400

    return render_template('index.html')

@app.route('/download/<path:filename>')
def download_file(filename):
    """文件下载路由"""
    safe_dir = os.path.abspath(os.path.join(get_base_path(), 'files'))
    file_path = os.path.abspath(os.path.join(get_base_path(), filename))
    
    # 防止路径穿越攻击
    if not file_path.startswith(safe_dir):
        return "非法文件路径", 403
    
    if os.path.isfile(file_path):
        return send_from_directory(
            directory=os.path.dirname(file_path),
            path=os.path.basename(file_path),
            as_attachment=True
        )
    return "文件不存在", 404

@app.route('/files')
def get_files():
    """获取文件列表接口"""
    return jsonify(get_file_list())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)