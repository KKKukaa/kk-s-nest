import os
import sys
import re
import json
import requests
import random
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_from_directory
from jinja2 import ChoiceLoader, FileSystemLoader

app = Flask(__name__)

# 为什么我的版本号都是整数？我不知道，但马上就不是整数了！v2.1堂堂登场！
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

# 配置模板加载器
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

def parse_message_file(filepath):
    """解析单个留言文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        username = re.search(r'Username: (.+)', content).group(1)
        time = re.search(r'Time: (.+)', content).group(1)
        message = re.search(r'Message:\n(.+)', content, re.DOTALL).group(1).strip()
        
        return {
            'username': username,
            'time': time,
            'message': message
        }
    except Exception as e:
        app.logger.error(f"解析文件 {filepath} 失败: {str(e)}")
        return None

def get_random_messages():
    """获取随机留言"""
    try:
        all_files = [f for f in os.listdir(mail_dir) if f.endswith('.txt')]
        random.shuffle(all_files)
        selected_files = all_files[:4]
        
        messages = []
        for filename in selected_files:
            filepath = os.path.join(mail_dir, filename)
            if msg := parse_message_file(filepath):
                messages.append(msg)
        
        # 补充空白消息
		# deekseek觉得这里是AI生成的重灾区
        empty_messages = ['好冷清啊', '果然没人啊', '默默哭泣中']
        while len(messages) < 4:
            messages.append({
                'username': 'KUK',
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'message': random.choice(empty_messages)
            })
            
        return messages
    except Exception as e:
        app.logger.error(f"获取留言失败: {str(e)}")
        return []

def call_deepseek_api(question):
    """调用API"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-reasoner",
        "messages": [{"role": "user", "content": question[:300]}]  # 限制问题长度
    }
    
	# 更详细的错误提示，爱来自v2.1
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        return "请求超时"
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            app.logger.critical("API密钥失效！")
            return "服务暂时不可用"
        return f"接口返回错误：{e.response.status_code}"
    except json.JSONDecodeError:
        return "响应解析失败，请联系管理员"
    except Exception as e:
        app.logger.error(f"未处理异常: {traceback.format_exc()}")
        return "系统繁忙"

def get_file_list():
    """可下载文件列表"""
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

# 为什么我要放这么多无关的注释？因为deek说这样可以减少人机味
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
                return jsonify({'error': '用户名过长'}), 400
            if len(message) > 500:
                return jsonify({'error': '消息过长'}), 400
            save_message(username, message)
            return jsonify({'status': 'success'})

        # 处理AI提问
        if question:
            if len(question) > 300:
                return jsonify({'error': '问题过长'}), 400
            answer = call_deepseek_api(question)
            return jsonify({'answer': answer})

        return jsonify({'error': '无效请求'}), 400

    # GET请求时传递留言数据
    messages = get_random_messages()
    return render_template('index.html', messages=messages)

@app.route('/download/<path:filename>')
def download_file(filename):
    """文件下载路由"""
    safe_dir = os.path.abspath(os.path.join(get_base_path(), 'files'))
    file_path = os.path.abspath(os.path.join(get_base_path(), filename))
    
    # 防止路径穿越攻击
	# deekseek觉得只有这里人类写的，其实这里才是AI写的
    if not file_path.startswith(safe_dir):
        return "I'm a teapot", 418
    
    if os.path.isfile(file_path):
        return send_from_directory(
            directory=os.path.dirname(file_path),
            path=os.path.basename(file_path),
            as_attachment=True
        )
    return "文件不存在，因为我是茶壶", 418

# 现在是2:21，手机坏了，悲伤
@app.route('/files')
def get_files():
    """获取文件列表"""
    return jsonify(get_file_list())

@app.route('/messages')
def get_messages():
    """获取留言"""
    return jsonify(get_random_messages())

# 手机又好了
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)