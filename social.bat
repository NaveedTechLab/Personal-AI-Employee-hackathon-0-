@echo off
cd /d "%~dp0"
call venv-win\Scripts\activate.bat

echo ============================================================
echo   Social Media Posting - AI Employee
echo ============================================================
echo.
echo   1. Generate LinkedIn Post (AI writes it)
echo   2. Generate Twitter Post (AI writes it)
echo   3. Generate ALL Platforms
echo   4. Post LinkedIn Draft
echo   5. Post Twitter Draft
echo   6. Post ALL Drafts
echo   7. Quick Post to LinkedIn (type your text)
echo   8. Quick Post to Twitter (type your text)
echo   9. Show Pending Drafts
echo   0. Exit
echo.
echo ============================================================

:menu
echo.
set /p choice="Select option (1-9): "

if "%choice%"=="1" (
    echo.
    set /p topic="Topic (press Enter for auto): "
    if "%topic%"=="" (
        python post_social.py --generate linkedin
    ) else (
        python post_social.py --generate linkedin --topic "%topic%"
    )
    goto menu
)

if "%choice%"=="2" (
    echo.
    set /p topic="Topic (press Enter for auto): "
    if "%topic%"=="" (
        python post_social.py --generate twitter
    ) else (
        python post_social.py --generate twitter --topic "%topic%"
    )
    goto menu
)

if "%choice%"=="3" (
    echo.
    set /p topic="Topic (press Enter for auto): "
    if "%topic%"=="" (
        python post_social.py --generate all
    ) else (
        python post_social.py --generate all --topic "%topic%"
    )
    goto menu
)

if "%choice%"=="4" (
    echo.
    echo Pending LinkedIn drafts:
    dir /b demo_vault\Pending_Approval\SOCIAL_linkedin_*.md 2>nul
    echo.
    set /p file="File name: "
    python post_social.py --platform linkedin --file "demo_vault\Pending_Approval\%file%"
    goto menu
)

if "%choice%"=="5" (
    echo.
    echo Pending Twitter drafts:
    dir /b demo_vault\Pending_Approval\SOCIAL_twitter_*.md 2>nul
    echo.
    set /p file="File name: "
    python post_social.py --platform twitter --file "demo_vault\Pending_Approval\%file%"
    goto menu
)

if "%choice%"=="6" (
    echo.
    echo Posting ALL pending drafts...
    for %%f in (demo_vault\Pending_Approval\SOCIAL_*.md) do (
        echo Posting: %%f
        python post_social.py --platform all --file "%%f"
    )
    goto menu
)

if "%choice%"=="7" (
    echo.
    set /p text="Type your LinkedIn post: "
    python post_social.py --platform linkedin --text "%text%"
    goto menu
)

if "%choice%"=="8" (
    echo.
    set /p text="Type your Twitter post: "
    python post_social.py --platform twitter --text "%text%"
    goto menu
)

if "%choice%"=="9" (
    echo.
    echo === Pending Drafts ===
    dir /b demo_vault\Pending_Approval\SOCIAL_*.md 2>nul || echo No pending drafts.
    echo.
    echo === Recently Posted ===
    dir /b demo_vault\Done\POSTED_*.md 2>nul || echo No recent posts.
    goto menu
)

if "%choice%"=="0" exit

goto menu
