import os
import sys
import re
import json
import requests
import random
import traceback
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_from_directory
from jinja2 import ChoiceLoader, FileSystemLoader

app = Flask(__name__)

# v2.2堂堂登场！
# 加入了更多配置文件，自定义更方便了
# 增加了对茶壶和咖啡的支持，204行旁边，不喜欢可以改掉
def get_base_path():  # 笑点解析：疯狂报错，找了一圈才发现引用在前定义在后。已修复
    """获取运行路径"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def load_config():
    config_path = os.path.join(get_base_path(), 'config.json')
    default_config = {
        "deepseek_api_key": "your-API-Key",
        "empty_messages": ["好冷清啊", "果然没人啊", "默默哭泣中"],
        "downloads": []
    }
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default_config

config = load_config()

# 额外的API Key
DEEPSEEK_API_KEY = config.get("deepseek_api_key", "your-API-Key")  # 如果配置不存在就回退
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

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
        
        # 从配置文件读取，如果没有就回退默认值
        empty_messages = config.get("empty_messages", ["暂无消息", "彩蛋"])
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
        "model": "deepseek-reasoner",  # 也可以用deepseek-chat也就是V3
        "messages": [{"role": "user", "content": question[:300]}]  # 限制问题长度
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        return "请求超时"
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            app.logger.critical("API密钥失效，请联系管理员")
            return "服务不可用"
        return f"接口返回错误：{e.response.status_code}"
    except json.JSONDecodeError:
        return "响应解析失败，请联系管理员"
    except Exception as e:
        app.logger.error(f"未处理异常: {traceback.format_exc()}")
        return "系统繁忙"  # 我不知道这些提示的意义是什么，我觉得大部分人不会把deepseek功能打开

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

# 无聊
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
	# dickseek觉得只有这里人类写的
    if not file_path.startswith(safe_dir):
        return "I'm a teapot", 418  # 这里是对茶壶的支持
    
    if os.path.isfile(file_path):
        return send_from_directory(
            directory=os.path.dirname(file_path),
            path=os.path.basename(file_path),
            as_attachment=True
        )
    return "没有这种咖啡！可接受的咖啡：冰美式", 406  # 对咖啡壶的支持

@app.route('/files')
def get_files():
    """获取文件列表"""
    return jsonify(get_file_list())

@app.route('/messages')
def get_messages():
    """获取留言"""
    return jsonify(get_random_messages())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)  # 这个debug感觉迄今为止没有用到过                                                                                                                                                      我是彩蛋：问了一圈，没有AI觉得这是人写的！我真的很人机吗