@echo off
echo ========================================
echo API Test Framework v2.0 - Enterprise Edition
echo ========================================
echo.

echo Installing/Updating dependencies...
python -m pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org
python -m pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org

echo.
echo Starting test execution...
python run_tests.py run --scenario fullset_basic --requests 10

echo.
echo Test execution completed!
echo Check the output/reports folder for detailed results.
pause