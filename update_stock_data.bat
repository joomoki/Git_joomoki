@echo off
setlocal
chcp 65001 > nul
cd /d "%~dp0"

echo ==============================================
echo       주식 데이터 최신화 작업 (최종일자 삭제)
echo ==============================================
echo.

:: 1. 국내 주식 최신화 (최종일자 삭제 포함) 및 웹 내보내기
echo [1/1] 국내 주식 최신화 및 웹 반영 중...
python scripts\check_and_update_kr.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ [오류] 데이터 업데이트 중 오류가 발생했습니다.
    goto end
)

:: 참고: 미국 주식 최신화가 필요한 경우 아래 주석(::)을 제거하세요.
:: echo.
:: echo [확장] 미국 주식 최신화 중...
:: python scripts\maintenance\collect_us_stocks.py
:: if %errorlevel% neq 0 (
::     echo ❌ [오류] 미국 주식 데이터 업데이트 중 오류가 발생했습니다.
::     goto end
:: )

echo.
echo ==============================================
echo [2/3] D:\joomoki_PJ 의 index.html 을 D:\DataStock 에 배포합니다...

copy /Y D:\joomoki_PJ\index.html D:\DataStock\index.html
if %errorlevel% neq 0 (
    echo ❌ [오류] index.html 복사 중 오류가 발생했습니다.
    goto end
)

echo.
echo ==============================================
echo [3/3] GitHub 원격 저장소에 데이터 푸시 중...
echo ==============================================

echo.
echo [DataStock 저장소 푸시]
cd /d D:\DataStock
git add .
git commit -m "Auto update portal data and UI"
git push origin main
if %errorlevel% neq 0 (
    echo ❌ [오류] D:\DataStock GitHub 푸시 중 오류가 발생했습니다.
    goto end
)

echo.
echo [joomoki_PJ 저장소 푸시]
cd /d D:\joomoki_PJ
git add index.html update_stock_data.bat
git commit -m "Update UI and deployment script"
git push origin HEAD
if %errorlevel% neq 0 (
    echo ❌ [오류] D:\joomoki_PJ GitHub 푸시 중 오류가 발생했습니다.
    goto end
)

echo.
echo ✅ [성공] 데이터 갱신, UI 배포, GitHub 푸시 작업이 모두 완료되었습니다!
echo ==============================================
:end
echo.
pause
