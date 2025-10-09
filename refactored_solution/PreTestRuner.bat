@echo off
echo Starting the execution..
echo Installing/Updating dependencies...
python -m pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org
python -m pip install requests --trusted-host pypi.org --trusted-host files.pythonhosted.org
python -m pip install openpyxl --trusted-host pypi.org --trusted-host files.pythonhosted.org
python -m pip install pandas --trusted-host pypi.org --trusted-host files.pythonhosted.org

echo Starting test execution...
python main_runner.py test --data-type both

echo Test execution completed!
echo Check the Report folder for detailed results.
pause
echo Executed successfully..
pause