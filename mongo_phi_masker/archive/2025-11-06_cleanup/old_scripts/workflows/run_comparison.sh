#!/bin/bash
echo "Running MongoDB collection comparison..."
cd "$(dirname "$0")/.."
source ./venv/Scripts/activate
python scripts/simple_compare.py > comparison_results.txt 2>&1
echo "Results saved to comparison_results.txt"
echo "Displaying results:"
cat comparison_results.txt
