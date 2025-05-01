# Change Tracking Checklist

## Database Changes
- [ ] Add field to database model in `EP_database.py`
- [ ] Create migration script in `migrations/` directory
- [ ] Test migration script on test database
- [ ] Verify field is nullable or has default value
- [ ] Add field to database tests in `test_database.py`
- [ ] Update database documentation

## API Changes
- [ ] Add field to API request/response models in `EP_api.py`
- [ ] Update API validation logic
- [ ] Add field to API tests in `test_api.py`
- [ ] Update API documentation
- [ ] Verify backward compatibility
- [ ] Test API endpoints with new field

## Web Application Changes
- [ ] Add field to form in `templates/errands.html`
- [ ] Update form validation in `web_app.py`
- [ ] Add field to route handling in `web_app.py`
- [ ] Update error handling for new field
- [ ] Add field to web application tests in `test_web_app.py`
- [ ] Update web application documentation

## Frontend Changes
- [ ] Add field to form display
- [ ] Add field to form validation
- [ ] Update form submission handling
- [ ] Add field to error messages
- [ ] Update success messages
- [ ] Test form submission with new field
- [ ] Verify field persistence after page refresh

## Testing Requirements
- [ ] Create test cases for new field
- [ ] Test field validation
- [ ] Test field persistence
- [ ] Test field relationships
- [ ] Test error handling
- [ ] Test edge cases
- [ ] Update existing tests to include new field

## Documentation Updates
- [ ] Update database schema documentation
- [ ] Update API documentation
- [ ] Update user documentation
- [ ] Update developer documentation
- [ ] Update implementation tracker
- [ ] Update architecture documentation

## Relationship Management
- [ ] Update related models
- [ ] Update relationship handling
- [ ] Test relationship persistence
- [ ] Test relationship validation
- [ ] Update relationship documentation
- [ ] Test relationship edge cases

## Security Considerations
- [ ] Verify field access permissions
- [ ] Update input validation
- [ ] Test for SQL injection
- [ ] Test for XSS vulnerabilities
- [ ] Update security documentation

## Performance Impact
- [ ] Test database performance
- [ ] Test API performance
- [ ] Test web application performance
- [ ] Update indexes if needed
- [ ] Document performance considerations

## Deployment Checklist
- [ ] Create deployment script
- [ ] Test deployment on staging
- [ ] Create rollback plan
- [ ] Document deployment steps
- [ ] Update version numbers
- [ ] Update changelog

## Example: Adding a New Field
1. Database:
   ```python
   # EP_database.py
   class Errand(Base):
       new_field = Column(String, nullable=True)
   ```

2. Migration:
   ```python
   # migrations/add_new_field.py
   def migrate():
       db_session.execute(text("""
           ALTER TABLE errands 
           ADD COLUMN new_field VARCHAR(255)
       """))
   ```

3. API:
   ```python
   # EP_api.py
   class ErrandCreate(BaseModel):
       new_field: Optional[str] = None
   ```

4. Web App:
   ```python
   # web_app.py
   def errands():
       new_field = request.form.get('new_field')
       # Handle new field
   ```

5. Template:
   ```html
   <!-- templates/errands.html -->
   <input type="text" name="new_field" value="{{ errand.new_field if errand else '' }}">
   ```

## Example: Adding a Relationship
1. Database:
   ```python
   # EP_database.py
   class Errand(Base):
       related_errands = Column(String)  # Comma-separated list of IDs
   ```

2. API:
   ```python
   # EP_api.py
   class ErrandUpdate(BaseModel):
       related_errands: Optional[List[int]] = None
   ```

3. Web App:
   ```python
   # web_app.py
   def errands():
       related_errands = request.form.getlist('related_errands[]')
       # Update both sides of relationship
       for related_id in related_errands:
           related_errand = db_session.query(Errand).get(related_id)
           if related_errand:
               # Update both errands
   ```

4. Template:
   ```html
   <!-- templates/errands.html -->
   <select name="related_errands[]" multiple>
       {% for errand in errands %}
           <option value="{{ errand.id }}">{{ errand.title }}</option>
       {% endfor %}
   </select>
   ```

## Notes
- Always test changes in a development environment first
- Keep track of all modified files
- Document any breaking changes
- Consider backward compatibility
- Update all relevant tests
- Verify all relationships are properly maintained
- Check for performance impact
- Ensure proper error handling
- Update all documentation 