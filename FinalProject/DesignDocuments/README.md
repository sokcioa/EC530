# Errand Planner

An intelligent errand planning system that helps users optimize their daily tasks and errands by integrating with Google Calendar and Maps.

## Features

- Google Calendar integration for schedule management
- Location-based errand optimization
- Flexible scheduling with customizable time windows
- Support for multiple transportation modes (Drive, Bus, Bike, Walk)
- Intelligent route planning and optimization
- Recurring errand support with flexible intervals

## Setup

### Prerequisites

1. Python 3.9 or higher
2. Google Cloud Platform account
3. Enabled APIs in Google Cloud Console:
   - Google Calendar API
   - Google Maps Platform APIs (Places, Directions)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd FinalProject
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up Google Cloud credentials:
   1. Go to [Google Cloud Console](https://console.cloud.google.com)
   2. Create a new project or select an existing one
   3. Enable the required APIs:
      - Google Calendar API
      - Google Maps Platform APIs
   4. Create OAuth 2.0 credentials:
      - Go to APIs & Services > Credentials
      - Create OAuth 2.0 Client ID
      - Download the client configuration
      - Save as `credentials.json` in the project directory

## Components

### Google Authentication (`google_auth.py`)

Handles authentication with Google APIs for calendar and maps access.

Features:
- OAuth 2.0 authentication flow
- Token persistence
- Automatic token refresh
- Scope verification for Calendar and Maps APIs

Usage:
```python
from google_auth import GoogleAuth

# Create auth handler with default scopes
auth = GoogleAuth()

# Get credentials
credentials = auth.get_credentials()

# Verify access
if auth.verify_calendar_access():
    print("Calendar access granted")
if auth.verify_maps_access():
    print("Maps access granted")
```

### Testing

Run the test suite:
```bash
python test_google_auth.py
```

The test suite includes:
- Unit tests for authentication initialization
- Scope verification tests
- Live authentication testing (requires `credentials.json`)

Note: Some tests will be skipped if `credentials.json` is not present.

## Project Structure

- `google_auth.py`: Google API authentication handler
- `test_google_auth.py`: Test suite for authentication
- `requirements.txt`: Python dependencies
- `Architecture.txt`: System architecture and design
- `README.md`: This documentation

## Development Status

- [x] Google Authentication Implementation
- [x] Test Suite
- [ ] Calendar Integration
- [ ] Maps Integration
- [ ] Errand Planning Algorithm
- [ ] User Interface 