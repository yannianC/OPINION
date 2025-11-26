@echo off
chcp 65001 >nul
echo ========================================
echo Opinion Trade 自动化控制台
echo ========================================
echo.

cd /d %~dp0

if not exist "node_modules" (
    echo 检测到未安装依赖，正在使用阿里镜像源安装...
    echo.
    call npm install --registry=https://registry.npmmirror.com
    echo.
    echo 依赖安装完成！
    echo.
)

echo 正在启动开发服务器...
echo.
echo 服务器将在 http://localhost:3000 启动
echo 按 Ctrl+C 可停止服务器
echo.
echo ========================================
echo.

call npm run dev

pause

