#!/bin/bash
set -e
echo "Starting IoT Data Visualization for Smart Cities..."
uvicorn app:app --host 0.0.0.0 --port 9064 --workers 1
