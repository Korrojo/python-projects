@echo off
echo Checking masking status at %date% %time% > masking_status.txt
echo. >> masking_status.txt

echo === Process Check === >> masking_status.txt
tasklist | findstr python >> masking_status.txt
echo. >> masking_status.txt

echo === Recent Log Files === >> masking_status.txt
dir /b /o-d logs\preprod\masking_*.log >> masking_status.txt
echo. >> masking_status.txt

echo === Latest Log File Content (last 10 lines) === >> masking_status.txt
type logs\preprod\masking_20250701_044004.log | tail -10 >> masking_status.txt
echo. >> masking_status.txt

echo Status check complete. Results saved to masking_status.txt
