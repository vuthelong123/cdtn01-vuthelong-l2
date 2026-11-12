@echo off
chcp 65001 >nul
title Mekong Mobile Warranty Management - BT2
echo =======================================================================
echo     HE THONG QUAN LY YEU CAU BAO HANH - MEKONG MOBILE (BT2)
echo     Sinh vien: Vu The Long - MSSV: 2374802010286
echo =======================================================================
echo.

echo [BUOC 1/3] Kiem tra va cai dat thu vien tu requirements.txt...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Khong the cai dat thu vien. Vui long kiem tra lai moi truong Python / pip.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [BUOC 2/3] Chay kiem thu tu dong (61/61 Tests)...
pytest -v
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CANH BAO] Co test khong vuot qua.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [BUOC 3/3] Khoi chay Web Server...
echo (He thong tu dong tao Database va nap du lieu mau, khong can cai MySQL!)
echo.
python src\main.py

pause
