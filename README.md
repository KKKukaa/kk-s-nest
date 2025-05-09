# KUK的小窝 - 多功能Web门户

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Flask Version](https://img.shields.io/badge/flask-2.0%2B-lightgrey)
![License](https://img.shields.io/badge/license-WTFPL-green)

**一个简单的Web应用，可以当做资源站用？**

## ❗ 注意，本程序为新手的初次尝试，如有不足请见谅

## 🌟 功能亮点

- **消息存储系统**
  - 用户认证留言功能
  - 自动过滤危险字符
  - 留言存档按时间/用户名分类
- **DeepSeek AI**
  - 此功能已隐藏
- **安全文件共享**
  - 动态加载下载列表
  - 防路径穿越攻击
  - 文件大小显示
- **留言墙**
  - 自动读取留言
  - 不知道该写什么 
- **便捷部署**
  - 一键EXE打包

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
或者在 wrap.bat 和 run.bat 中二选一，效果也是一样的

# 🔍 如何启用DeepSeek AI功能

## 1. 注册

前往[DeepSeek官网](https://deepseek.com/)注册账号，获取API Key。

## 2. 修改文件

在 app.py 中修改 DEEPSEEK_API_KEY 为你的API Key

## 3. 修改HTML文件

找到在 html 文件夹中的 index.html ，修改名称或者删除

## 4. 启动项目

```bash
python app.py
```
或使用 wrap.bat 快捷打包

## 5. 访问

启动程序后，访问 http://127.0.0.1:5000/ 即可查看网页

# ‼️ 额外说明

- 程序会优先检查html文件夹中的index.html文件，如果存在则直接显示，否则会显示默认的网页(templates/index.html)
- 修改html文件夹中的index.html文件后，需要重启程序才能生效
- config.json 文件实际上是记录可以被下载的文件，如果你想要分享新文件，必须修改这个文件，然后重启程序
- 我写死的只能下载files里的文件，不然就是非法的
- 以及，本库中的所有网页都是deepseek写的
- 留言墙默认只读取4条留言，如果想修改有点麻烦，还是在app.py里
- 由于我比较懒，其实很多功能本来应该搞成可以用配置文件的，但是懒得写了
- wrap.bat 可以把程序快捷打包成exe文件，但是其实直接 python app.py 也是一样的
- run.bat 人如其名，就是直接运行
- 这些规则纯粹是我不知道写在哪，所以就先这样了