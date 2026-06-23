@echo off
cls
echo ================================================
echo          EPUB转TXT工具 v2.1 - 启动脚本
 echo ================================================
echo.

REM 检查Python是否安装
echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.6+
    echo [提示] 建议从官网下载最新版本：https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查pip是否可用
echo 检查pip工具...
pip --version >nul 2>&1
if errorlevel 1 (
    echo [错误] pip不可用，请确保Python安装正确
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖包...
pip show ebooklib >nul 2>&1
if errorlevel 1 (
    echo [提示] 依赖包未安装，正在安装...
    echo [进度] 正在安装必要的依赖包，请稍候...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖包安装失败
        echo [提示] 请检查网络连接或手动运行：pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo [成功] 依赖包安装完成！
)

echo [启动] 正在启动EPUB转TXT工具...
echo [提示] 首次启动可能需要一些时间，请耐心等待...
python epub_to_txt_converter.py

if errorlevel 1 (
    echo [错误] 工具启动失败
    echo [提示] 请检查错误信息并尝试重新启动
    pause
    exit /b 1
)

pause