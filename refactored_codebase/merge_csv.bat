@echo off
echo ========================================
echo API Test Framework v2.0 - CSV Merger
echo ========================================
echo.

echo Installing/Updating dependencies...
python -m pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org
python -m pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org

echo.
set /p csv_folder="Enter the CSV folder name to merge: "

echo.
echo Merging CSV files from %csv_folder%...
python run_tests.py merge %csv_folder% --format-type excel

echo.
echo CSV merge completed!
echo Check the output/merged folder for Excel reports.
pause