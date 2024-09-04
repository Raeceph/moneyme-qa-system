#!/bin/bash

# Check if we're running in CLI mode
if [ "$1" = "cli" ]; then
    # Run the CLI application
    PYTHONPATH=/app python /app/src/cli_app.py "${@:2}"
else
    # Run the API server
    uvicorn src.api.app:app --host 0.0.0.0 --port 8000
fi