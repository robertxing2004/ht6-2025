@echo off
REM Set up QNX SDP environment for cross-compilation
set QNX_HOST=C:\QNX700\host\win64\x86_64
set QNX_TARGET=C:\QNX700\target\qnx7
set PATH=%QNX_HOST%\usr\bin;%PATH%

REM Set target architecture for Raspberry Pi 4B (ARM64)
set QNX_ARCH=aarch64
set QNX_CC=aarch64-unknown-nto-qnx710-gcc
set QNX_CXX=aarch64-unknown-nto-qnx710-g++
set QNX_AR=aarch64-unknown-nto-qnx710-ar
set QNX_LD=aarch64-unknown-nto-qnx710-ld

echo QNX SDP environment configured for ARM64 cross-compilation
