pip install PyInstaller -i https://mirrors.aliyun.com/pypi/simple/
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
pyinstaller --onefile --add-data "templates;templates"  --hidden-import=email.mime.application app.py