@echo off
chcp 65001 > nul
title CaseLaw MCP Installer

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-for-novice.ps1"

if errorlevel 1 (
    echo.
    echo [ERROR] Installation failed.
    echo Please report at: https://github.com/lapiogga/caseLaw/issues
    pause
)
