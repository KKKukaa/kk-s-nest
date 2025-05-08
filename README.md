# KUK的小窝 - 多功能Web门户

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Flask Version](https://img.shields.io/badge/flask-2.0%2B-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

**一个简单的Web应用，可以当做资源站用？**

## ‼️ 注意，本程序为新手的初次尝试，如有不足请见谅

## 🌟 功能亮点

- **消息存储系统**
  - 用户认证留言功能
  - 自动过滤危险字符
  - 留言存档按时间/用户名分类
- **DeepSeek AI集成**
  - 此功能已隐藏
- **安全文件共享**
  - 动态加载下载列表
  - 防路径穿越攻击
  - 文件大小显示
- **便捷部署**
  - 一键EXE打包
  - 内网穿透支持
  - 跨平台兼容

## 🛠️ 技术栈

| 组件          | 技术实现                  |
|---------------|--------------------------|
| 后端框架      | Python Flask             |
| 前端设计      | HTML5/CSS3 + 现代动画    |
| API集成       | DeepSeek官方接口         |
| 安全方案      | 输入过滤 + 路径验证      |
| 部署方案      | PyInstaller + 内网穿透   |

## 🚀 快速开始

### 环境要求
- Python 3.8+
- pip 20.0+

### 安装步骤
```bash
# 克隆仓库
git clone https://github.com/yourusername/kuk-portal.git

# 进入项目目录
cd kuk-portal

# 安装依赖
pip install -r requirements.txt
```


# 如何启用deepseek AI功能

### 1. 注册DeepSeek账号

前往[DeepSeek官网](https://deepseek.com/)注册账号，获取API Key和Secret Key。

### 2. 修改配置文件

在 app.py 中修改 DEEPSEEK_API_KEY 为你的API Key

### 3. 启动项目

```bash
python app.py
```
### 4. 更换HTML文件

在 templates 文件夹中找到 2.html ，移动至 html 文件夹中，并修改名称为 index.html ，替换原文件