# Temporary Test Scripts: Deletion and Archiving

---
description: Ensure temporary test scripts are deleted or archived to keep the codebase clean
globs: *.py,*.sh
alwaysApply: false
---

## Overview

Temporary test scripts are often created during development for various purposes:
- Debugging specific issues
- Testing new features or APIs
- Exploring library functionality
- Performance profiling
- Data migration

While these scripts are valuable during development, they should not clutter the codebase permanently.

## Guidelines

### Script Creation
- Place temporary scripts in a designated directory (e.g., `tests/debug/` or `scripts/temp/`)
- Add a clear comment header explaining:
  - Purpose of the script
  - Related issue/PR number
  - Expected lifetime
  - Dependencies and setup required
- Example:
  ```python
  """
  Temporary script to debug user authentication flow
  Related to: #123
  Created: 2024-05-01
  Expected lifetime: Until PR #123 is merged
  Dependencies: pytest, requests
  """
  ```

### Script Management
- Review temporary scripts weekly
- Delete scripts that are no longer needed
- Archive valuable scripts that might be useful later
- Never commit temporary scripts to main branches
- Add temporary script directories to `.gitignore`

### When to Keep vs. Delete
**Keep (Archive) if:**
- Script contains valuable debugging patterns
- Script demonstrates complex API usage
- Script includes performance optimization techniques
- Script might be needed for similar issues in future

**Delete if:**
- Issue has been resolved
- Better solution has been implemented
- Script was for one-time data migration
- Script is no longer compatible with current codebase

### Archiving Process
1. Move script to `scripts/archive/` directory
2. Update script header with:
   - Resolution of the original issue
   - Date of archival
   - Any relevant documentation links
3. Add to script index (if maintained)

### Example Archive Header
```python
"""
ARCHIVED: 2024-05-15
Originally created to debug user auth flow (#123)
Issue resolved by implementing proper token refresh
See docs/auth_configuration.md for current implementation
"""
```

## Best Practices
- Never use temporary scripts in production
- Document any insights gained in proper documentation
- Convert useful patterns into proper test cases
- Keep archive directory organized by category/date
- Regularly clean up archived scripts (e.g., quarterly) 