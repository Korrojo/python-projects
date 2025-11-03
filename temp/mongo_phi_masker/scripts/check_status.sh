#!/bin/bash

echo "Checking masking status at $(date)" > masking_status.txt
echo "" >> masking_status.txt

echo "=== Process Check ===" >> masking_status.txt
ps -ef | grep python | grep -v grep >> masking_status.txt
echo "" >> masking_status.txt

echo "=== Recent Log Files ===" >> masking_status.txt
ls -lt logs/preprod/masking_*.log | head -5 >> masking_status.txt
echo "" >> masking_status.txt

echo "=== Latest Log File Content (last 10 lines) ===" >> masking_status.txt
tail -10 logs/preprod/masking_20250701_044004.log >> masking_status.txt 2>/dev/null
echo "" >> masking_status.txt

echo "Status check complete. Results saved to masking_status.txt"
