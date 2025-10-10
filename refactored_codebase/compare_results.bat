@echo off
echo ========================================
echo API Test Framework v2.0 - Batch Comparison
echo ========================================
echo.

set /p pre_folder="Enter pre-test folder name: "
set /p post_folder="Enter post-test folder name: "

echo.
echo Comparing %pre_folder% vs %post_folder%...
python run_tests.py batch-compare %pre_folder% %post_folder% --detailed

echo.
echo Comparison completed!
echo Check the output/comparisons folder for detailed comparison reports.
pause