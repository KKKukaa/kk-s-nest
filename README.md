# KUK的小窝 - 多功能Web门户

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)  
![Flask Version](https://img.shields.io/badge/flask-2.0%2B-lightgrey)  
![License](https://img.shields.io/badge/license-WTFPL-green)

**一个轻量级Web应用，集成资源分享、消息存储与AI功能**  
❗ *注意：本项目为新手实践作品，功能与代码仍在优化中，欢迎指正。*

---

## 🌟 核心功能

### **消息存储系统**
- 用户认证留言功能（需登录）
- 自动过滤危险字符（XSS/SQLi防护）
- 留言存档支持按时间、用户名分类检索

### **安全文件共享**
- 动态加载下载列表（仅限 *files/* 目录）
- 防路径穿越攻击，实时校验文件合法性
- 文件大小自动计算与展示  
  *📌 新增文件需在* config.json *中注册并重载配置*

### **DeepSeek AI集成**（默认关闭）
- 通过官方API实现对话功能  
  *📌 需在[DeepSeek官网](https://deepseek.com/)注册并配置API Key*

### **留言墙**
- 自动读取最新4条留言（数量需修改 app.py 调整）
- 实时展示用户留言  
  *📌 修改HTML文件后需重启服务生效*

### **便捷部署**
- 一键EXE打包（通过 *package.bat* ）
- 支持内网穿透快速部署
- 提供 *run.bat* 直接启动服务

---

## 🛠️ 技术实现

| 模块          | 方案                          |
|---------------|------------------------------|
| 后端框架      | Flask 2.0+                   |
| 前端设计      | HTML5/CSS3 + 动态交互        |
| 安全机制      | 输入过滤 + 路径白名单校验    |
| API集成       | DeepSeek官方接口             |
| 部署方案      | PyInstaller + 内网穿透       |

---

## 🚀 快速部署

### 环境要求
- Python 3.8+
- pip 20.0+

### 启动步骤
```bash
git clone https://github.com/KKKukaa/kk-s-nest.git
cd kk-s-nest
pip install -r requirements.txt

# 方式1: 直接运行
python app.py

# 方式2: 使用脚本
run.bat        # 启动服务
package.bat    # 生成EXE文件
```

### 启用DeepSeek AI
1. 在[DeepSeek官网](https://deepseek.com/)获取API Key
2. 修改 *config.json* 中的 *DEEPSEEK_API_KEY*
3. 删除或重命名 html/index.html 以启用AI页面
4. 重启服务

---

## 📝 注意事项

1. **页面优先级**  
   程序优先加载 *html/index.html* ，若不存在则使用 *templates/index.html* 

2. **文件安全**  
   所有可下载文件必须存放在 *files/* 目录并在 *config.json* 中注册

3. **配置生效**  
   - 修改HTML文件或配置文件后需**重启服务**
   - 部分功能（如留言显示数量）需直接修改 *app.py*

4. **开发说明**  
   - 前端页面由DeepSeek生成
   - 部分配置项尚未模块化，后续计划优化

访问 http://127.0.0.1:5000/ 开始使用 ▶