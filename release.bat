@echo off
set /p VERSION="Nhap so phien ban moi (vi du v1.0.1): "

echo ----------------------------------------------------
echo [1/3] Dang tu dong build code tu may cua ban...
echo ----------------------------------------------------
docker compose -f docker-compose.prod.yml build

echo ----------------------------------------------------
echo [2/3] Dang gan tag so %VERSION% cho cac image...
echo ----------------------------------------------------
docker tag ntnhan1801/echoscene-backend:latest ntnhan1801/echoscene-backend:%VERSION%
docker tag ntnhan1801/echoscene-frontend:latest ntnhan1801/echoscene-frontend:%VERSION%

echo ----------------------------------------------------
echo [3/3] Dang push ca hai ban latest va %VERSION% len Docker Hub...
echo ----------------------------------------------------
docker compose -f docker-compose.prod.yml push
docker push ntnhan1801/echoscene-backend:%VERSION%
docker push ntnhan1801/echoscene-frontend:%VERSION%

echo ----------------------------------------------------
echo 🎉 Xong roi! Ban %VERSION% va latest da duoc day len Docker Hub.
echo ----------------------------------------------------
pause
