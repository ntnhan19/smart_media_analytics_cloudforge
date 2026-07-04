@echo off
chcp 65001 >nul
echo ========================================================
echo        KHOI DONG SMART MEDIA ANALYTICS CLOUDFORGE
echo ========================================================
echo.

echo [1/3] Dang khoi dong Docker Containers (Chay ngam)...
docker-compose up -d

echo.
echo [2/3] Dang cho he thong khoi dong... (Khoang 10 giay)
timeout /t 10 /nobreak >nul

echo.
echo [3/3] Dang mo trinh duyet...
start http://localhost:5173

echo.
echo ========================================================
echo Tat ca da hoan tat! Ban co the tat cua so nay.
echo ========================================================
pause
