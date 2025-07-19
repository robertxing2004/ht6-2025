# QNX Cross-Compilation PowerShell Script for Windows
# Fixed version for QNX 8.0

Write-Host '========================================' -ForegroundColor Green
Write-Host "QNX Cross-Compilation for Raspberry Pi 4B" -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Green

# Set QNX environment variables
$env:QNX_HOST = "C:\Users\Daniel\qnx800\host\win64\x86_64"
$env:QNX_TARGET = "C:\Users\Daniel\qnx800\target\qnx"
$env:PATH = "$env:QNX_HOST\usr\bin;$env:PATH"

Write-Host "Setting up QNX SDP environment..." -ForegroundColor Yellow
Write-Host "QNX_HOST: $env:QNX_HOST" -ForegroundColor Cyan
Write-Host "QNX_TARGET: $env:QNX_TARGET" -ForegroundColor Cyan

# Check if QNX compiler exists
$qnxCompiler = "$env:QNX_HOST\usr\bin\aarch64-unknown-nto-qnx8.0.0-g++.exe"
if (-not (Test-Path $qnxCompiler)) {
    Write-Host "ERROR: QNX compiler not found at $qnxCompiler" -ForegroundColor Red
    exit 1
}

Write-Host "QNX compiler found: $qnxCompiler" -ForegroundColor Green

# Compiler flags for QNX 8.0
$CXXFLAGS = "-Wall -Wextra -std=c++11 -O2 -pthread"
$CXXFLAGS += " -D_QNX_SOURCE"
$CXXFLAGS += " -D_REENTRANT"
$CXXFLAGS += " -D_POSIX_C_SOURCE=200809L"
$CXXFLAGS += " -I$env:QNX_TARGET\usr\include"
$CXXFLAGS += " -I$env:QNX_TARGET\usr\include\aarch64"

# Linker flags (simplified - only use essential libraries)
$LDFLAGS = "-L$env:QNX_TARGET\usr\lib"
$LDFLAGS += " -L$env:QNX_TARGET\usr\lib\aarch64"

# Use only essential QNX libraries that are available
$LIBS = "-lsocket"

Write-Host "Building for QNX 8.0 ARM64..." -ForegroundColor Yellow

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "*.o") { Remove-Item "*.o" -Force }
if (Test-Path "listener.exe") { Remove-Item "listener.exe" -Force }
if (Test-Path "battery_monitor.exe") { Remove-Item "battery_monitor.exe" -Force }
if (Test-Path "test_client.exe") { Remove-Item "test_client.exe" -Force }
if (Test-Path "battery_ai_predictor.exe") { Remove-Item "battery_ai_predictor.exe" -Force }

# Function to compile a source file
function Compile-Source {
    param([string]$SourceFile)
    
    Write-Host "Compiling $SourceFile..." -ForegroundColor Cyan
    
    # Create proper object file name
    $objectFile = $SourceFile.Replace('.cpp', '.o')
    $compileCmd = "& `"$qnxCompiler`" $CXXFLAGS -c `"$SourceFile`" -o `"$objectFile`""
    Write-Host "Command: $compileCmd" -ForegroundColor Gray
    
    Invoke-Expression $compileCmd
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to compile $SourceFile" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Function to link object files
function Link-Objects {
    param([string]$ObjectFile, [string]$OutputFile, [string]$AdditionalLibs = "")
    
    Write-Host "Linking $OutputFile..." -ForegroundColor Cyan
    
    $linkCmd = "& `"$qnxCompiler`" $LDFLAGS `"$ObjectFile`" $LIBS $AdditionalLibs -o `"$OutputFile`""
    Write-Host "Command: $linkCmd" -ForegroundColor Gray
    
    Invoke-Expression $linkCmd
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to link $OutputFile" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Build targets
$success = $true

# Build listener
Write-Host "Building listener..." -ForegroundColor Green
if (Compile-Source "listener.cpp") {
    if (Link-Objects "listener.o" "listener.exe") {
        Write-Host '✓ listener.exe built successfully' -ForegroundColor Green
    } else { 
        $success = $false 
    }
} else { 
    $success = $false 
}

# Build battery_monitor
Write-Host "Building battery_monitor..." -ForegroundColor Green
if (Compile-Source "battery_monitor.cpp") {
    if (Link-Objects "battery_monitor.o" "battery_monitor.exe") {
        Write-Host '✓ battery_monitor.exe built successfully' -ForegroundColor Green
    } else { 
        $success = $false 
    }
} else { 
    $success = $false 
}

# Skip battery_ai_predictor for now (JSON dependency issues)
Write-Host "Skipping battery_ai_predictor (JSON dependency not available)" -ForegroundColor Yellow

# Clean up object files
if (Test-Path "*.o") { Remove-Item "*.o" -Force }

if ($success) {
    Write-Host ""
    Write-Host '========================================' -ForegroundColor Green
    Write-Host 'Build successful!' -ForegroundColor Green
    Write-Host '========================================' -ForegroundColor Green
    Write-Host ""
    Write-Host "Generated binaries:" -ForegroundColor Yellow
    Get-ChildItem "*.exe" | ForEach-Object { Write-Host "  $($_.Name)" -ForegroundColor Cyan }
    Write-Host ""
    Write-Host "To deploy to Raspberry Pi:" -ForegroundColor Yellow
    Write-Host "1. Copy the .exe files to your QNX target" -ForegroundColor White
    Write-Host "2. Rename .exe to remove extension on QNX" -ForegroundColor White
    Write-Host "3. Make executable: chmod +x filename" -ForegroundColor White
    Write-Host ""
    Write-Host "Note: battery_ai_predictor was skipped due to JSON dependency" -ForegroundColor Yellow
    Write-Host "Note: test_client was skipped due to function name conflict" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host '========================================' -ForegroundColor Red
    Write-Host 'Build failed!' -ForegroundColor Red
    Write-Host '========================================' -ForegroundColor Red
    exit 1
}