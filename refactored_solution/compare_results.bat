@echo off
echo ========================================
echo Enhanced API Testing Framework
echo Result Comparison Tool
echo ========================================
echo.

set /p pre_folder="Enter pre-test folder name: "
set /p post_folder="Enter post-test folder name: "

echo.
echo Comparing %pre_folder% vs %post_folder%...
python main_runner.py compare --pre-folder %pre_folder% --post-folder %post_folder%

echo.
echo Comparison completed!
echo Check the CompareResult folder for detailed comparison reports.
pause