@echo off
REM Visual Studio Build Script for Windows
REM This will compile the code for Windows testing

echo ========================================
echo Visual Studio Build for Windows Testing
echo ========================================

REM Set up Visual Studio environment
echo Setting up Visual Studio environment...
call "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to set up Visual Studio environment
    echo Please install Visual Studio Build Tools 2022
    exit /b 1
)

echo Visual Studio environment set up successfully

REM Clean previous builds
echo Cleaning previous builds...
if exist *.obj del *.obj
if exist *.exe del *.exe

REM Compiler flags for MSVC
set CXXFLAGS=/std:c++11 /O2 /W3 /EHsc

echo Building with MSVC compiler...

REM Build listener
echo Building listener...
cl %CXXFLAGS% listener.cpp /Fe:listener.exe
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build listener
    exit /b 1
)

REM Build battery_monitor
echo Building battery_monitor...
cl %CXXFLAGS% battery_monitor.cpp /Fe:battery_monitor.exe
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build battery_monitor
    exit /b 1
)

REM Build test_client
echo Building test_client...
cl %CXXFLAGS% test_client.cpp /Fe:test_client.exe
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build test_client
    exit /b 1
)

REM Build battery_ai_predictor (skip curl for now)
echo Building battery_ai_predictor...
cl %CXXFLAGS% battery_ai_predictor.cpp /Fe:battery_ai_predictor.exe
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
echo listener.exe
echo battery_monitor.exe
echo test_client.exe 