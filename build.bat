@echo off
echo バルク管理ラベル発行アプリをビルドしています...
pyinstaller build.spec
echo.
if exist "dist\バルク管理ラベル発行\バルク管理ラベル発行.exe" (
    echo ビルド完了: dist\バルク管理ラベル発行\バルク管理ラベル発行.exe
) else (
    echo ビルドに失敗しました
)
pause
