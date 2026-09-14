@echo off
chcp 949 >nul
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHON_EXE=.venv\Scripts\python.exe"
set "APP_PATH=src\as_report\app.py"
set "PORT=8501"
set "MODE=%~1"

if /I "%MODE%"=="--local" goto ENSURE_ENV
if /I "%MODE%"=="--host" goto ENSURE_ENV
if /I "%MODE%"=="--repair" goto ENSURE_ENV
if /I "%MODE%"=="--check" goto ENSURE_ENV
if not "%MODE%"=="" goto INVALID_OPTION

:MENU
cls
echo ==================================================
echo              A/S 리포트 실행 도구
echo ==================================================
echo.
echo   1. 내 PC에서 실행
echo   2. 팀 공유 모드로 실행
echo   3. 실행환경 복구
echo   0. 종료
echo.
set /p "MENU_CHOICE=번호를 선택하세요: "
if "%MENU_CHOICE%"=="1" set "MODE=--local"
if "%MENU_CHOICE%"=="2" set "MODE=--host"
if "%MENU_CHOICE%"=="3" set "MODE=--repair"
if "%MENU_CHOICE%"=="0" exit /b 0
if not defined MODE (
    echo.
    echo 올바른 번호를 선택해 주세요.
    pause
    goto MENU
)

:ENSURE_ENV
if exist "%PYTHON_EXE%" goto ENV_READY

echo.
echo Python 실행환경을 처음 준비합니다.
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m venv .venv
) else (
    where python >nul 2>nul
    if errorlevel 1 goto PYTHON_NOT_FOUND
    python -m venv .venv
)
if errorlevel 1 goto ENV_ERROR

"%PYTHON_EXE%" -m pip install -e .
if errorlevel 1 goto INSTALL_ERROR

:ENV_READY
if /I "%MODE%"=="--repair" goto REPAIR
if /I "%MODE%"=="--check" goto CHECK
if /I "%MODE%"=="--host" goto HOST
goto LOCAL

:CHECK
"%PYTHON_EXE%" -c "import sys; sys.path.insert(0, 'src'); import as_report, streamlit; from as_report.report_presentation import PPT_TEMPLATE_PATH, PRESENTATION_BUILDER_PATH; assert PPT_TEMPLATE_PATH.is_file(); assert PRESENTATION_BUILDER_PATH.is_file(); print('AS Report environment: OK')"
exit /b %errorlevel%

:REPAIR
echo.
echo 실행환경을 확인하고 필요한 패키지를 다시 설치합니다.
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 goto INSTALL_ERROR
"%PYTHON_EXE%" -m pip install -e .
if errorlevel 1 goto INSTALL_ERROR
echo.
echo 실행환경 복구가 완료됐습니다.
pause
exit /b 0

:LOCAL
echo.
echo 브라우저에서 A/S 리포트 도구를 엽니다.
echo 주소: http://localhost:%PORT%
echo 종료하려면 이 창에서 Ctrl+C를 누르세요.
echo.
"%PYTHON_EXE%" -m streamlit run "%APP_PATH%" --server.port %PORT%
goto SERVER_END

:HOST
netstat -ano -p tcp | findstr /R /C:":%PORT% .*LISTENING" >nul
if not errorlevel 1 (
    echo.
    echo 포트 %PORT%가 이미 사용 중입니다.
    echo 기존 Streamlit 창을 종료한 뒤 다시 실행해 주세요.
    pause
    exit /b 1
)
echo.
echo 팀 공유 모드로 실행합니다.
echo 이 PC와 같은 사내 네트워크의 팀원에게 http://이_PC의_IP:%PORT% 주소를 알려주세요.
echo 생성 파일은 실행 PC에서 처리되며, 방화벽 설정은 자동으로 변경하지 않습니다.
echo 종료하려면 이 창에서 Ctrl+C를 누르세요.
echo.
"%PYTHON_EXE%" -m streamlit run "%APP_PATH%" --server.address 0.0.0.0 --server.port %PORT%

:SERVER_END
echo.
echo Streamlit이 종료되었습니다.
pause
exit /b 0

:INVALID_OPTION
echo 지원하지 않는 옵션입니다: %MODE%
echo 사용 가능 옵션: --local, --host, --repair, --check
exit /b 2

:PYTHON_NOT_FOUND
echo.
echo Python 3을 찾을 수 없습니다.
echo Python 3.10 이상을 설치한 뒤 다시 실행해 주세요.
pause
exit /b 1

:ENV_ERROR
echo.
echo Python 가상환경 생성에 실패했습니다.
pause
exit /b 1

:INSTALL_ERROR
echo.
echo 필요한 패키지 설치에 실패했습니다.
echo 네트워크와 Python 설치 상태를 확인해 주세요.
pause
exit /b 1
