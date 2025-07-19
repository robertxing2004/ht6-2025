@echo off
echo ========================================
echo Compiling Battery Monitor for Windows
echo ========================================

REM Try to find Visual Studio compiler
set "VS_PATH=C:\Program Files\Microsoft Visual Studio\2022\BuildTools"
set "VC_PATH=%VS_PATH%\VC\Tools\MSVC"

REM Find the MSVC version directory
for /d %%i in ("%VC_PATH%\*") do (
    if exist "%%i\bin\Hostx64\x64\cl.exe" (
        set "CL_PATH=%%i\bin\Hostx64\x64\cl.exe"
        goto :found
    )
)

echo ERROR: Visual Studio compiler not found
echo Please install Visual Studio Build Tools 2022
pause
exit /b 1

:found
echo Found compiler: %CL_PATH%

REM Clean previous builds
echo Cleaning previous builds...
if exist *.obj del *.obj
if exist *.exe del *.exe

REM Compiler flags
set CXXFLAGS=/std:c++11 /O2 /W3 /EHsc

echo Building with Visual Studio compiler...

REM Build listener
echo Building listener...
"%CL_PATH%" %CXXFLAGS% listener.cpp /Fe:listener.exe
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build listener
    pause
    exit /b 1
)

REM Build battery_monitor
echo Building battery_monitor...
"%CL_PATH%" %CXXFLAGS% battery_monitor.cpp /Fe:battery_monitor.exe
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build battery_monitor
    pause
    exit /b 1
)

REM Build test_client
echo Building test_client...
"%CL_PATH%" %CXXFLAGS% test_client.cpp /Fe:test_client.exe
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build test_client
    pause
    exit /b 1
)

REM Build battery_ai_predictor (without curl for now)
echo Building battery_ai_predictor...
"%CL_PATH%" %CXXFLAGS% battery_ai_predictor.cpp /Fe:battery_ai_predictor.exe
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Failed to build battery_ai_predictor (curl dependency)
    echo This is expected if curl is not installed
)

echo.
echo ========================================
echo Build completed!
echo ========================================
echo.
echo Generated binaries:
dir *.exe
echo.
echo NOTE: These are Windows executables for testing
echo For QNX cross-compilation, install QNX SDP 8.0
echo.
echo To test the programs:
echo   listener.exe
echo   battery_monitor.exe
echo   test_client.exe
echo.
pause 