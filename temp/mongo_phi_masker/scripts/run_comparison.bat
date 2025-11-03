@echo off
echo Running MongoDB collection comparison...
cd /d %~dp0\..
call venv\Scripts\activate.bat
python scripts\simple_compare.py > comparison_results.txt 2>&1
echo Results saved to comparison_results.txt
