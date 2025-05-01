# Errand Planner Codebase Restructuring Plan

## Current State
The codebase is currently in a monolithic structure with the following main components:

### Core Application
- `web_app.py` (43KB) - Main application with routes and business logic
- `google_auth.py` (3.9KB) - Google OAuth2 authentication and session management
- `cert.pem` and `key.pem` - SSL certificates for secure connections in https

### Database Layer
- `EP_database.py` (11KB) - Database models and operations
- `errands.db` - SQLite database file
- `migrations/` - Database migration scripts

### API Integrations
- `EP_places.py` (5.1KB) - Places API integration
- `places_api.py` (7.7KB) - Places API implementation
- `EP_directions.py` (6.7KB) - Directions API integration
- `EP_api.py` (5.3KB) - Base API functionality

### User Interface
- `EP_calendar_window.py` (7.4KB) - Calendar functionality
- `EP_personal_info.py` (5.5KB) - User profile management
- `EP_errands_window.py` (16KB) - Errand management
- `templates/` - HTML templates for the web interface

### Testing
- `test_web_app.py` (38KB) - Main application tests
- `test_directions_api.py` (7.9KB) - Directions API tests
- `test_api.py` (6.0KB) - API tests
- `test_database.py` (5.3KB) - Database tests
- `test_google_auth.py` (1.5KB) - Authentication tests
- `EP_test_api.py` (6.5KB) - Additional API tests
- `EP_test_database.py` (5.3KB) - Additional database tests

### Documentation and Tracking
- `implementation_tracker.md` - Implementation progress tracking
- `change_tracking.md` - Change history
- `logs/` - Application logs
- `DesignDocuments/` - Design documentation and planning

### Draft Work
- `Draft/` - Directory containing work in progress and refactoring attempts

## Proposed Structure
```
FinalProject/
├── api/
│   ├── __init__.py
│   ├── auth.py
│   ├── errands.py
│   ├── users.py
│   └── calendar.py
├── services/
│   ├── __init__.py
│   ├── errand_service.py
│   ├── user_service.py
│   ├── address_service.py
│   ├── directions_service.py
│   └── places_service.py
├── validators/
│   ├── __init__.py
│   ├── errand_validator.py
│   ├── address_validator.py
│   ├── user_validator.py
│   └── time_validator.py
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── errand.py
│   └── calendar.py
├── config/
│   ├── __init__.py
│   ├── app_config.py
│   ├── database_config.py
│   ├── logging_config.py
│   └── api_config.py
├── utils/
│   ├── __init__.py
│   ├── address_utils.py
│   ├── time_utils.py
│   ├── error_handlers.py
│   └── api_utils.py
├── templates/
├── static/
├── tests/
│   ├── __init__.py
│   ├── test_errands.py
│   ├── test_users.py
│   ├── test_auth.py
│   ├── test_calendar.py
│   ├── test_directions.py
│   └── test_places.py
└── app.py
```

## Implementation Checklist

### Phase 1: Core Infrastructure
- A: [x] Create new directory structure
  - [x] Create `api/` directory
  - [x] Create `services/` directory
  - [x] Create `validators/` directory
  - [x] Create `models/` directory
  - [x] Create `config/` directory
  - [x] Create `utils/` directory
  - [x] Create `tests/` directory
  - [x] Create `templates/` directory
  - [x] Create `static/` directory
  - [x] Verify: Directory structure exists

### Phase 2: API Layer Migration
- A: [x] Migrate Base API
  - [x] Create `api/__init__.py`
  - [x] Move `EP_api.py` to `api/base.py`
  - [x] Update imports in all files
  - [x] Verify: Run `test_api.py` 

- B: [x] Migrate Places API
  - [x] Create `api/places.py`
  - [x] Update `api/__init__.py`
  - [x] Update imports in all files
  - [x] Verify: Run `test_places_api.py`

- C: [x] Migrate Directions API
  - [x] Create `api/directions.py`
  - [x] Move functionality from `EP_directions.py`
  - [x] Update imports in all files
  - [x] Verify: Run `test_directions_api.py`

- D: [x] Migrate Authentication
  - [x] Create `api/auth.py`
  - [x] Move functionality from `google_auth.py`
  - [x] Update imports in all files
  - [x] Verify: Run `test_google_auth.py`

### Phase 3: Database Layer Migration
- A: [x] Migrate Base Models
  - [x] Create `models/__init__.py`
  - [x] Create `models/base.py`
  - [x] Move base model code from `EP_database.py`
  - [x] Update imports in all files
  - [x] Verify: Run `test_database.py` and `EP_test_database.py`
  - [x] Fix database initialization in tests
  - [x] Update test cases to match model fields
  - [x] Verify: All 4 database tests passing

- B: [x] Migrate User Model
  - [x] Create `models/user.py`
  - [x] Move user-related code from `EP_database.py`
  - [x] Update imports in all files
  - [x] Verify: Run `test_web_app.py` (user-related tests)

- C: [x] Migrate Errand Model
  - [x] Create `models/errand.py`
  - [x] Move errand-related code from `EP_database.py`
  - [x] Update imports in all files
  - [x] Verify: Run `test_web_app.py` (errand-related tests)

- D: [x] Migrate Database Configuration
  - [x] Create `config/database_config.py`
  - [x] Move database configuration from `EP_database.py`
  - [x] Update imports in all files
  - [x] Verify: Run all database tests

### Phase 4: Service Layer Migration
- A: [x] Migrate Errand Service
  - [x] Create `services/errand_service.py`
  - [x] Move errand-related business logic from `EP_errands_window.py`
  - [x] Update imports in all files
  - [x] Verify: Run `test_web_app.py` (errand-related tests)

- B: [ ] Migrate User Service
  - [ ] Create `services/user_service.py`
  - [ ] Move user-related business logic from `EP_personal_info.py`
  - [ ] Update imports in all files
  - [ ] Verify: Run `test_web_app.py` (user-related tests)

- C: [ ] Migrate Calendar Service
  - [ ] Create `services/calendar_service.py`
  - [ ] Move calendar-related business logic from `EP_calendar_window.py`
  - [ ] Update imports in all files
  - [ ] Verify: Run `test_web_app.py` (calendar-related tests)

### Phase 5: Validation Layer Migration
- A: [ ] Migrate Errand Validation
  - [ ] Create `validators/errand_validator.py`
  - [ ] Move validation logic from `EP_errands_window.py`
  - [ ] Update imports in all files
  - [ ] Verify: Run `test_web_app.py` (errand validation tests)

- B: [ ] Migrate User Validation
  - [ ] Create `validators/user_validator.py`
  - [ ] Move validation logic from `EP_personal_info.py`
  - [ ] Update imports in all files
  - [ ] Verify: Run `test_web_app.py` (user validation tests)

- C: [ ] Migrate Address Validation
  - [ ] Create `validators/address_validator.py`
  - [ ] Move validation logic from `EP_places.py`
  - [ ] Update imports in all files
  - [ ] Verify: Run `test_web_app.py` (address validation tests)

### Phase 6: Configuration Migration
- A: [ ] Migrate App Configuration
  - [ ] Create `config/app_config.py`
  - [ ] Move configuration from `web_app.py`
  - [ ] Update imports in all files
  - [ ] Verify: Run `test_web_app.py`

- B: [ ] Migrate Logging Configuration
  - [ ] Create `config/logging_config.py`
  - [ ] Move logging configuration from `web_app.py`
  - [ ] Update imports in all files
  - [ ] Verify: Check log files for proper formatting

-C: [ ] Migrate API Configuration
  - [ ] Create `config/api_config.py`
  - [ ] Move API configuration from various files
  - [ ] Update imports in all files
  - [ ] Verify: Run all API tests

### Phase 7: Utility Migration
- A: [ ] Migrate Address Utilities
  - [ ] Create `utils/address_utils.py`
  - [ ] Move address-related utilities from `EP_places.py`
  - [ ] Update imports in all files
  - [ ] Verify: Run `test_web_app.py` (address-related tests)

- B: [ ] Migrate Time Utilities
  - [ ] Create `utils/time_utils.py`
  - [ ] Move time-related utilities from various files
  - [ ] Update imports in all files
  - [ ] Verify: Run `test_web_app.py` (time-related tests)

- C: [ ] Migrate Error Handlers
  - [ ] Create `utils/error_handlers.py`
  - [ ] Move error handling from various files
  - [ ] Update imports in all files
  - [ ] Verify: Run `test_web_app.py` (error handling tests)

### Phase 8: Test Migration
- A: [ ] Migrate API Tests
  - [ ] Create `tests/test_api.py`
  - [ ] Move tests from `test_api.py` and `EP_test_api.py`
  - [ ] Update imports
  - [ ] Verify: Run all API tests

- B: [ ] Migrate Database Tests
  - [ ] Create `tests/test_database.py`
  - [ ] Move tests from `test_database.py` and `EP_test_database.py`
  - [ ] Update imports
  - [ ] Verify: Run all database tests

- C: [ ] Migrate Integration Tests
  - [ ] Create `tests/test_web_app.py`
  - [ ] Move tests from current `test_web_app.py`
  - [ ] Update imports
  - [ ] Verify: Run all integration tests

### Phase 9: Cleanup
- A: [ ] Move all Old Files to /depticated
  - [ ] Move all `EP_*.py` files
  - [ ] Move old test files
  - [ ] Verify: No references to old files exist outside of /depricated

- B: [ ] Update Documentation
  - [ ] Update README
  - [ ] Update requirements.txt
  - [ ] Update deployment scripts
  - [ ] Verify: Documentation is up to date

## Testing Strategy
Each migration step includes a verification step that runs relevant tests. The tests are organized as follows:

1. **API Tests**
   - `test_api.py`
   - `EP_test_api.py`
   - `test_directions_api.py`
   - `test_google_auth.py`

2. **Database Tests**
   - `test_database.py`
   - `EP_test_database.py`

3. **Integration Tests**
   - `test_web_app.py`

4. **Component-Specific Tests**
   - User-related tests
   - Errand-related tests
   - Calendar-related tests
   - Address-related tests
   - Time-related tests
   - Error handling tests

## Migration Strategy
1. Each step is self-contained and testable
2. Tests are run after each migration step
3. If tests fail, fix issues before proceeding
4. Keep old files until all tests pass
5. Remove old files only after successful migration

## Timeline
Each phase is estimated to take 1-2 days, with testing included in each step.

Total estimated time: 9-18 days

## Benefits

1. **Improved Maintainability**
   - Smaller, focused files
   - Clear separation of concerns
   - Easier to locate and fix issues

2. **Better Testability**
   - Components can be tested in isolation
   - Clearer test boundaries
   - More focused test cases

3. **Enhanced Scalability**
   - New features can be added without modifying existing code
   - Easier to add new API endpoints
   - Better support for future extensions

4. **Improved Debugging**
   - Issues can be isolated to specific modules
   - Clearer error messages
   - Better logging structure

## Risks and Mitigation

1. **Risk**: Breaking existing functionality
   - **Mitigation**: Comprehensive test suite
   - **Mitigation**: Phased implementation
   - **Mitigation**: Regular testing during migration

2. **Risk**: Performance impact
   - **Mitigation**: Profile critical paths
   - **Mitigation**: Optimize database queries
   - **Mitigation**: Cache where appropriate

3. **Risk**: Development slowdown
   - **Mitigation**: Clear documentation
   - **Mitigation**: Training for team members
   - **Mitigation**: Code review process 