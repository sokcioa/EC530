#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Redis P2P Chat Application...${NC}"

# Start Redis server
echo -e "${YELLOW}Starting Redis server...${NC}"
redis-server --daemonize yes

# Wait for Redis to start
sleep 2

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}Failed to start Redis server${NC}"
    exit 1
fi

echo -e "${GREEN}Redis server is running${NC}"

# Start the FastAPI application
echo -e "${YELLOW}Starting FastAPI application...${NC}"
python main.py

# Note: You'll need to create a main.py file that imports and sets up your FastAPI app 