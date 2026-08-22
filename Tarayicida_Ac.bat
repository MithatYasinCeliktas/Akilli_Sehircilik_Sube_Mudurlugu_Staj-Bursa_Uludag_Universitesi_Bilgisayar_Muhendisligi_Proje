@echo off
for /f "delims=" %%I in ('powershell -command "(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias Wi-Fi, Ethernet -ErrorAction SilentlyContinue | Select-Object -First 1).IPAddress"') do set "IP=%%I"
if "%IP%"=="" set "IP=localhost"
start http://%IP%:4200/