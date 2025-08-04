@echo off
echo ================= Gerando Executável =================

REM Navegar até a pasta do projeto
cd /d "%~dp0"

REM Deletar pastas antigas
rmdir /s /q build
rmdir /s /q dist
del /q main.spec

REM Criar novo arquivo .spec incluindo os módulos ocultos
pyi-makespec --noconsole --onefile main.py

REM Adicionar dependências manuais ao .spec (ou edite direto, como mostrei antes)

REM Gerar o executável
pyinstaller main.spec

echo.
echo ✅ Executável criado em: dist\main.exe
pause