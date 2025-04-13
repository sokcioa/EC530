#!/usr/bin/env python3
import os
import sys
import unittest
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the test runner"""
    parser = argparse.ArgumentParser(description='Run Directory Server tests')
    parser.add_argument('-t', '--test', help='Specific test file to run')
    parser.add_argument('-v', '--verbose', action='store_true', help='Run tests in verbose mode')
    parser.add_argument('--host', default='127.0.0.1', help='Directory server host')
    parser.add_argument('--port', type=int, default=5000, help='Directory server port')
    parser.add_argument('--start-server', action='store_true', 
                        help='Start a new server for testing (instead of using an existing one)')
    
    args = parser.parse_args()
    
    # Set environment variables for the tests
    if args.host:
        os.environ['DIRECTORY_SERVER_HOST'] = args.host
    if args.port:
        os.environ['DIRECTORY_SERVER_PORT'] = str(args.port)
    if args.start_server:
        os.environ['START_SERVER'] = 'true'
    
    logger.info("Starting Directory Server tests...")
    if args.start_server:
        logger.info("Starting a new directory server for testing")
    else:
        logger.info(f"Using existing directory server at {args.host}:{args.port}")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the directory to the Python path
    sys.path.insert(0, script_dir)
    
    # Set up test discovery
    if args.test:
        # Run a specific test file
        test_suite = unittest.TestLoader().loadTestsFromName(args.test)
    else:
        # Discover and run all tests
        test_suite = unittest.TestLoader().discover(script_dir, pattern='test_*.py')
    
    # Run the tests
    verbosity = 2 if args.verbose else 1
    result = unittest.TextTestRunner(verbosity=verbosity).run(test_suite)
    
    # Return the exit code based on test results
    exit_code = 0 if result.wasSuccessful() else 1
    
    if exit_code == 0:
        logger.info("All tests passed successfully!")
    else:
        logger.error("Some tests failed. See above for details.")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 