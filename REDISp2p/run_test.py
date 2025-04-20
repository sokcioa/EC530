#!/usr/bin/env python3
import subprocess
import sys
import time
import os
import signal
import atexit

def run_test():
    print("Starting Redis P2P Chat test...")
    
    # Check if Redis is running
    try:
        subprocess.run(["redis-cli", "ping"], check=True, capture_output=True)
        print("✅ Redis is running")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ Redis is not running. Please start Redis first.")
        print("   On macOS: brew services start redis")
        print("   On Linux: sudo systemctl start redis")
        sys.exit(1)
    
    # Run the test script
    print("\nRunning test script...")
    test_process = subprocess.Popen(
        [sys.executable, "TestTopicServer.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Function to handle cleanup
    def cleanup():
        if test_process.poll() is None:
            print("\nTerminating test process...")
            test_process.terminate()
            try:
                test_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                test_process.kill()
    
    # Register cleanup function
    atexit.register(cleanup)
    
    # Handle keyboard interrupt
    def signal_handler(sig, frame):
        print("\nTest interrupted by user")
        cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Stream output from the test process
    while True:
        line = test_process.stdout.readline()
        if not line and test_process.poll() is not None:
            break
        print(line, end="")
    
    # Get the return code
    return_code = test_process.wait()
    
    if return_code == 0:
        print("\n✅ Test completed successfully")
    else:
        print(f"\n❌ Test failed with return code {return_code}")
        sys.exit(return_code)

if __name__ == "__main__":
    run_test() 