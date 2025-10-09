@echo off
echo ========================================
echo Enhanced API Testing Framework
echo CSV Merger Tool
echo ========================================
echo.

echo Installing/Updating dependencies...
python -m pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org
python -m pip install pandas --trusted-host pypi.org --trusted-host files.pythonhosted.org
python -m pip install openpyxl --trusted-host pypi.org --trusted-host files.pythonhosted.org

echo.
set /p csv_folder="Enter the CSV folder name to merge: "

echo.
echo Merging CSV files from %csv_folder%...
python main_runner.py merge --csv-folder %csv_folder%

echo.
echo CSV merge completed!
echo Check the MergedOut_File folder for Excel reports.
pause