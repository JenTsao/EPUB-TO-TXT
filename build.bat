@echo off
echo EPUB转TXT工具 - 打包脚本
echo ========================================

REM 检查PyInstaller是否安装
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo 错误: PyInstaller安装失败
        pause
        exit /b 1
    )
)

echo 清理之前的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo 开始打包...
pyinstaller --onefile --windowed --name="电子书转换工具" --clean epub_to_txt_converter.py

if errorlevel 1 (
    echo 错误: 打包失败
    pause
    exit /b 1
)

echo 移动exe文件...
if exist "dist\电子书转换工具.exe" (
    move "dist\电子书转换工具.exe" "电子书转换工具.exe"
    echo 成功生成: 电子书转换工具.exe
) else (
    echo 错误: 未找到生成的exe文件
    pause
    exit /b 1
)

echo 清理临时文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo.
echo ========================================
echo 打包完成！
echo 生成文件: 电子书转换工具.exe
echo 可以直接运行，无需Python环境
echo ========================================
pause