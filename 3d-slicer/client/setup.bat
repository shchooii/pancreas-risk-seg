@echo off
chcp 65001
cls

echo ========================================================
echo  3D Slicer 사용자 환경 자동 설정 도구
echo ========================================================
echo.
echo  현재 폴더의 설정 파일들을 사용자 홈 디렉터리로 복사합니다.
echo  복사 위치: %USERPROFILE%
echo.

:: 1. .slicerrc.py 복사 (기존 파일이 있으면 덮어씌움 /Y)
copy /Y "%~dp0.slicerrc.py" "%USERPROFILE%\.slicerrc.py"
if %errorlevel% neq 0 goto ERROR

:: 2. config.ini 복사
copy /Y "%~dp0config.ini" "%USERPROFILE%\config.ini"
if %errorlevel% neq 0 goto ERROR

:: 3. DICOMwebBrowser.py 복사
copy /Y "%~dp0DICOMwebBrowser.py" "%USERPROFILE%\DICOMwebBrowser.py"
if %errorlevel% neq 0 goto ERROR

echo.
echo ========================================================
echo  [성공] 모든 파일이 정상적으로 복사되었습니다.
echo  이제 3D Slicer를 실행하면 자동으로 설정이 적용됩니다.
echo ========================================================
pause
exit

:ERROR
echo.
echo  [오류] 파일 복사 중 문제가 발생했습니다.
pause