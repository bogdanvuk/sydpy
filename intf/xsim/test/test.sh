#!/bin/bash
set -e
python3 setup.py build_ext --inplace
echo "Compilation successfull!"
echo "Starting the test suite..."
python3 test.py
