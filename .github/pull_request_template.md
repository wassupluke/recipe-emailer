## Description

<!-- Provide a brief description of the changes in this PR -->

## Type of Change

<!-- Mark the appropriate option with an 'x' -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🎨 Code style update (formatting, renaming)
- [ ] ♻️ Code refactor (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] ✅ Test update
- [ ] 🔧 Build/CI update
- [ ] 🔒 Security fix

## Motivation and Context

<!-- Why is this change required? What problem does it solve? -->
<!-- If it fixes an open issue, please link to the issue here -->

Fixes # (issue)

## Changes Made

<!-- List the specific changes made in this PR -->

### Code Changes
- 
- 
- 

### Configuration Changes
- 
- 

### Documentation Changes
- 
- 

## Testing

### Test Coverage

<!-- Describe the tests you ran and how to reproduce them -->

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing locally
- [ ] Coverage meets target (≥95%)

**Coverage Report:**
```
Current coverage: X%
Target coverage: 95%
```

### Manual Testing

<!-- Describe any manual testing performed -->

**Steps to test:**
1. 
2. 
3. 

**Test environments:**
- [ ] Local development
- [ ] Debug mode (`-d` flag)
- [ ] Production mode

## Code Quality Checklist

<!-- Verify all items before requesting review -->

### Code Style
- [ ] ✅ Follows PEP 8 style guide
- [ ] ✅ Code formatted with Black
- [ ] ✅ Linting passes (Ruff)
- [ ] ✅ No unnecessary comments or debug code

### Type Safety
- [ ] ✅ All functions have type hints
- [ ] ✅ Mypy strict mode passes
- [ ] ✅ Type aliases used where appropriate
- [ ] ✅ No `Any` types unless necessary

### Documentation
- [ ] ✅ All new functions have docstrings
- [ ] ✅ Docstrings follow Google style
- [ ] ✅ Examples included in docstrings
- [ ] ✅ README updated (if needed)
- [ ] ✅ CHANGELOG updated

### Error Handling
- [ ] ✅ Custom exceptions used appropriately
- [ ] ✅ Error messages are clear and actionable
- [ ] ✅ Logging added at appropriate levels
- [ ] ✅ No silent failures

### Testing
- [ ] ✅ Edge cases covered
- [ ] ✅ Error conditions tested
- [ ] ✅ Integration tests for new features
- [ ] ✅ No flaky tests

## Performance Impact

<!-- Describe any performance impact of these changes -->

**Benchmarks:**

| Operation | Before | After | Change |
|-----------|--------|-------|--------|
| Example | Xs | Ys | ±Z% |

- [ ] No performance regression
- [ ] Performance improvement documented
- [ ] Benchmarks run and attached

## Breaking Changes

<!-- List any breaking changes and migration steps -->

**Breaking Changes:** (Yes/No)

If yes, describe:
- What breaks:
- Why it's necessary:
- Migration path:

## Dependencies

<!-- List any new dependencies or dependency updates -->

**New Dependencies:**
- None
- Or list them:
  - `package-name>=version` - Purpose

**Updated Dependencies:**
- None
- Or list them:
  - `package-name`: `old-version` → `new-version` - Reason

## Security Considerations

<!-- Describe any security implications -->

- [ ] No new security vulnerabilities introduced
- [ ] Security scan passes
- [ ] No hardcoded secrets
- [ ] Input validation added
- [ ] HTML/SQL injection prevention considered

## Deployment Notes

<!-- Any special deployment considerations -->

**Pre-deployment:**
- [ ] Environment variables updated (if needed)
- [ ] Database migrations ready (if needed)
- [ ] Configuration changes documented

**Deployment steps:**
1. 
2. 
3. 

**Rollback plan:**
1. 
2. 

## Screenshots/Examples

<!-- Add screenshots or code examples if applicable -->

**Before:**
```python
# Old code
```

**After:**
```python
# New code
```

## Reviewer Notes

<!-- Any specific areas you'd like reviewers to focus on -->

**Focus areas for review:**
- 
- 
- 

**Questions for reviewers:**
- 
- 

## Checklist

<!-- Final checklist before requesting review -->

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
- [ ] I have checked my code and corrected any misspellings

## Related PRs/Issues

<!-- Link related PRs or issues -->

- Related to #
- Depends on #
- Blocks #

---

**Additional Notes:**

<!-- Any other information that would be helpful for reviewers -->
