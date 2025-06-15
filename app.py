import os
import sys
import re
import json
import requests
import random
import traceback
import threading
import time
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_from_directory
from jinja2 import ChoiceLoader, FileSystemLoader

app = Flask(__name__)

print(r"""
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░██████░░██░░██░░██████░░░░██████░░██░░██░░██░░██████░░
░░░░██░░░░██░░██░░█░░░░░░░░░██░░░░░░██░░██░░██░░░░██░░░░░
░░░██░░░░██████░░██████░░░░██████░░██████░░██░░░░██░░░░░░
░░██░░░░██░░██░░█░░░░░░░░░░░░░██░░██░░██░░██░░░░██░░░░░░░
░██░░░░██░░██░░██████░░░░██████░░██░░██░░██░░░░██░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
""")


def get_base_path():
    """获取运行路径"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def load_config():
    """加载主配置文件"""
    config_path = os.path.join(get_base_path(), 'config.json')
    default_config = {
        "DEEPSEEK_API_KEY": "your-API-Key",
        "host": "0.0.0.0",
        "port": 5000,
        "debug": False,
        "max_username_length": 20,
        "max_message_length": 500,
        "max_question_length": 300,
        "empty_messages": ["好冷清啊", "果然没人啊", "默默哭泣中"],
        "downloads": []
    }
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
    except:
        return default_config


def save_config(config_data):
    """保存配置文件"""
    try:
        config_path = os.path.join(get_base_path(), 'config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存配置失败: {str(e)}")
        return False

config = load_config()
DEEPSEEK_API_KEY = config.get("deepseek_api_key", "your-API-Key")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

base_path = get_base_path()
external_template_dir = os.path.join(base_path, 'html')
default_template_dir = os.path.join(app.root_path, 'templates')

app.jinja_loader = ChoiceLoader([
    FileSystemLoader(external_template_dir),
    FileSystemLoader(default_template_dir)
])

mail_dir = os.path.join(get_base_path(), 'mail')
os.makedirs(mail_dir, exist_ok=True)

def sanitize_filename(filename):
    """清理危险字符"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def save_message(username, message):
    """保存消息到文件"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        max_len = config.get("max_username_length", 20)
        safe_username = sanitize_filename(username)[:max_len]
        filename = f"{timestamp}_{safe_username}.txt"
        filepath = os.path.join(mail_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Username: {safe_username}\n")
            f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            max_msg_len = config.get("max_message_length", 500)
            f.write(f"Message:\n{message[:max_msg_len]}\n")
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
        "model": "deepseek-reasoner",
        "messages": [{"role": "user", "content": question[:config.get("max_question_length", 300)]}]
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
        return "系统繁忙"

def get_file_list():
    """可下载文件列表"""
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

def add_download_file(file_path, display_name=None):
    """添加新的下载文件"""
    if not os.path.isfile(file_path):
        return False, "文件不存在"
    
    # 获取相对路径
    rel_path = os.path.relpath(file_path, get_base_path())
    
    # 设置显示名称
    name = display_name or os.path.basename(file_path)
    
    # 检查是否已存在
    for item in config['downloads']:
        if item['path'] == rel_path:
            return False, "文件已存在"
    
    # 添加到配置
    config['downloads'].append({
        'name': name,
        'path': rel_path
    })
    
    # 保存配置
    if save_config(config):
        return True, f"成功添加文件: {name} ({rel_path})"
    return False, "保存配置失败"

def remove_download_file(index):
    """根据序号删除下载文件"""
    try:
        index = int(index) - 1  # 转换为0-based索引
        if index < 0 or index >= len(config['downloads']):
            return False, "序号无效"
        
        removed_item = config['downloads'].pop(index)
        
        if save_config(config):
            return True, f"已删除文件: {removed_item['name']} ({removed_item['path']})"
        return False, "保存配置失败"
    except ValueError:
        return False, "序号必须是数字"
    except Exception as e:
        return False, f"删除失败: {str(e)}"

def console_command_listener():
    """控制台命令监听器"""
    print("\n控制台命令已启动，输入 'help' 查看可用命令")
    while True:
        try:
            cmd = input("> ").strip().lower()
            
            # 支持快捷指令（前3个字母）
            if cmd.startswith('add') and len(cmd) >= 3:
                cmd = 'addfile' + cmd[3:]
            elif cmd.startswith('del') and len(cmd) >= 3:
                cmd = 'delfile' + cmd[3:]
            elif cmd.startswith('lis') and len(cmd) >= 3:
                cmd = 'listfiles'
            elif cmd.startswith('rel') and len(cmd) >= 3:
                cmd = 'reload'
            elif cmd.startswith('exi') and len(cmd) >= 3:
                cmd = 'exit'
            elif cmd.startswith('hel') and len(cmd) >= 3:
                cmd = 'help'
            
            if cmd == 'help':
                print("可用命令:")
                print("  addfile/add <文件路径> [显示名称] - 添加新文件到下载列表")
                print("  delfile/del <序号> - 从下载列表删除文件")
                print("  listfiles/lis - 显示当前下载文件列表")
                print("  reload/rel - 重新加载配置文件")
                print("  exit/exi - 退出程序")
            
            elif cmd.startswith('addfile') or cmd.startswith('add '):
                parts = cmd.split(maxsplit=2)
                if len(parts) < 2:
                    print("用法: addfile <文件路径> [显示名称]")
                    continue
                
                # 处理快捷指令前缀
                file_path = parts[1] if cmd.startswith('addfile') else parts[0]
                display_name = parts[2] if len(parts) > 2 else None
                
                success, message = add_download_file(file_path, display_name)
                print(message)
            
            elif cmd.startswith('delfile') or cmd.startswith('del '):
                parts = cmd.split()
                if len(parts) < 2:
                    print("用法: delfile <序号>")
                    continue
                
                # 处理快捷指令前缀
                index_str = parts[1] if cmd.startswith('delfile') else parts[1]
                
                try:
                    index = int(index_str)
                except ValueError:
                    print("序号必须是整数")
                    continue
                
                success, message = remove_download_file(index)
                print(message)
            
            elif cmd == 'listfiles' or cmd == 'lis':
                files = get_file_list()
                if not files:
                    print("没有可下载文件")
                else:
                    print("当前下载文件列表:")
                    for i, file in enumerate(files, 1):
                        print(f"{i}. {file['name']} ({file['path']}) - {file['size']}字节")
            
            elif cmd == 'reload' or cmd == 'rel':
                global config
                config = load_config()
                print("配置已重新加载")
            
            elif cmd == 'exit' or cmd == 'exi':
                print("正在退出程序...")
                os._exit(0)
            
            else:
                print("未知命令，输入 'help' 查看帮助")
                
        except Exception as e:
            print(f"命令执行错误: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        message = request.form.get('message', '').strip()
        question = request.form.get('question', '').strip()

        if username and message:
            max_username = config.get("max_username_length", 20)
            max_message = config.get("max_message_length", 500)
            
            if len(username) > max_username:
                return jsonify({'error': f'用户名过长（最大{max_username}字符）'}), 400
            if len(message) > max_message:
                return jsonify({'error': f'消息过长（最大{max_message}字符）'}), 400
                
            save_message(username, message)
            return jsonify({'status': 'success'})

        if question:
            max_question = config.get("max_question_length", 300)
            if len(question) > max_question:
                return jsonify({'error': f'问题过长（最大{max_question}字符）'}), 400
                
            answer = call_deepseek_api(question)
            return jsonify({'answer': answer})

        return jsonify({'error': '无效请求'}), 400

    messages = get_random_messages()
    return render_template('index.html', messages=messages)

@app.route('/download/<path:filename>')
def download_file(filename):
    safe_dir = os.path.abspath(os.path.join(get_base_path(), 'files'))
    file_path = os.path.abspath(os.path.join(get_base_path(), filename))
    
    if not file_path.startswith(safe_dir):
        return "I'm a teapot", 418
    
    if os.path.isfile(file_path):
        return send_from_directory(
            directory=os.path.dirname(file_path),
            path=os.path.basename(file_path),
            as_attachment=True
        )
    return "文件不存在", 404

@app.route('/files')
def get_files():
    return jsonify(get_file_list())

@app.route('/messages')
def get_messages():
    return jsonify(get_random_messages())

if __name__ == '__main__':
    console_thread = threading.Thread(target=console_command_listener, daemon=True)
    console_thread.start()
    
    host = config.get("host", "0.0.0.0")
    port = config.get("port", 5000)
    debug = config.get("debug", False)
    
    print(f"服务器将在 {host}:{port} 启动")
    app.run(host=host, port=port, debug=debug)