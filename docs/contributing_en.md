[中文文档](contributing.md)

# 🤝 Contributing Guide

Thank you for your interest in contributing to Claude Code Notifier! This guide explains how to contribute effectively.

## 🎯 Ways to Contribute

### Code Contributions
- 🐛 Bug fixes
- ✨ New features
- 🚀 Performance optimizations
- 📝 Documentation improvements
- 🧪 Increase test coverage

### Non-code Contributions
- 🐛 Report issues
- 💡 Feature suggestions
- 📖 Documentation translation
- 🎨 UI/UX design
- 📢 Promote the project

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Requirements
- Python 3.8+
- Git
- Claude Code (latest)

# Clone repository
git clone https://github.com/your-repo/claude-code-notifier.git
cd claude-code-notifier

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install development dependencies
pip install -r requirements-dev.txt
pip install -e .
```

### 2. Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run code quality checks
flake8 src/ tests/
black --check src/ tests/
mypy src/

# Run performance tests
python tests/test_performance_benchmarks.py
```

### 3. Verify Installation

```bash
# CLI tool
claude-notifier --version

# Integration tests
python tests/run_all_tests.py
```

## 📋 Development Standards

### Code Style

We use the following tools to ensure code quality:

```bash
# Formatting
black src/ tests/

# Import sorting
isort src/ tests/

# Linting
flake8 src/ tests/

# Type checking
mypy src/
```

### Commit Message Convention

Use the Conventional Commits format: https://conventionalcommits.org/

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

Types:
- feat: new feature
- fix: bug fix
- docs: documentation
- style: formatting (non-functional changes)
- refactor: refactoring
- test: tests
- chore: tooling/build

Examples:
```bash
git commit -m "feat(channels): add WeChat Work support"
git commit -m "fix(dingtalk): resolve signature validation issue"
git commit -m "docs: update configuration guide"
```

### Branching Model

```bash
# Main branches
main           # stable releases
develop        # development branch

# Supporting branches
feature/xxx    # new features
bugfix/xxx     # bug fixes
hotfix/xxx     # urgent fixes
release/xxx    # release preparation
```

## 🐛 Issue Reporting

### Report a Bug

Use the Bug Report template:
https://github.com/your-repo/claude-code-notifier/issues/new?template=bug_report.md

```markdown
**Bug Description**
A clear and concise description of the bug.

**Steps to Reproduce**
1. Run '...'
2. Click '...'
3. Scroll to '...'
4. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g., macOS 12.6]
- Python: [e.g., 3.9.7]
- Claude Code: [e.g., 1.2.3]
- Project Version: [e.g., 0.8.5]

**Additional Info**
- Logs
- Config files
- Screenshots
```

### Feature Requests

Use the Feature Request template:
https://github.com/your-repo/claude-code-notifier/issues/new?template=feature_request.md

```markdown
**Feature description**
Describe the feature you want.

**Problem context**
What problem does this feature solve?

**Solution**
Describe your preferred solution.

**Alternatives**
Describe any alternatives you've considered.

**Additional info**
Any other context or screenshots.
```

## 💻 Development Workflow

### 1. Create a Feature Branch

```bash
# Create from develop
git checkout develop
git pull origin develop
git checkout -b feature/my-awesome-feature
```

### 2. Develop and Test

```bash
# Write code
# Write tests
# Ensure tests pass
python -m pytest tests/ -v

# Code quality checks
make lint  # or run flake8, black, mypy manually
```

### 3. Commit Your Changes

```bash
# Stage changes
git add .

# Commit (use conventional commits)
git commit -m "feat(channels): add Slack notification support"

# Push
git push origin feature/my-awesome-feature
```

### 4. Open a Pull Request

1. Go to the GitHub repository
2. Click "Compare & pull request"
3. Fill in the PR template
4. Await review

### Pull Request Template

```markdown
## Description of Changes
Briefly describe what this PR changes.

## Type of Change
- [ ] 🐛 Bug fix
- [ ] ✨ New feature
- [ ] 🔄 Refactor
- [ ] 📝 Docs update
- [ ] 🧪 Tests
- [ ] 🚀 Performance improvement

## Testing
- [ ] Existing tests pass
- [ ] New tests added
- [ ] Manual testing done

## Checklist
- [ ] Code follows project conventions
- [ ] Self-tested all changes
- [ ] Docs updated accordingly
- [ ] No breaking changes

## Screenshots (if applicable)
Attach screenshots if UI changes are involved.

## Additional Information
Any other relevant info.
```

## 🧪 Testing Guide

### Test Layout

```
tests/
├── conftest.py                     # pytest config and fixtures
├── test_basic_units.py             # basic unit tests
├── test_integration_flows.py       # integration tests
├── test_performance_benchmarks.py  # performance tests
├── test_system_validation.py       # system validation tests
├── test_intelligence.py            # intelligence component tests
├── test_monitoring.py              # monitoring tests
└── run_all_tests.py                # test runner
```

### Writing Tests

```python
import unittest
from unittest.mock import Mock, patch
from your_module import YourClass

class TestYourClass(unittest.TestCase):
    """Unit tests for YourClass"""
    
    def setUp(self):
        """Runs before each test"""
        self.config = {'enabled': True, 'param': 'value'}
        self.instance = YourClass(self.config)
    
    def test_initialization(self):
        """Initialization test"""
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.param, 'value')
    
    @patch('external_module.external_function')
    def test_with_mock(self, mock_function):
        """Mock usage example"""
        mock_function.return_value = True
        
        result = self.instance.method_that_calls_external()
        
        self.assertTrue(result)
        mock_function.assert_called_once()
    
    def tearDown(self):
        """Runs after each test"""
        pass
```

### Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html tests/

# Open report
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

Targets:
- Overall coverage > 85%
- Core modules > 90%
- New code = 100%

## 📖 Documentation Contributions

### Docs Structure

```
docs/
├── quickstart.md          # Quickstart
├── configuration.md       # Configuration
├── channels.md            # Channels
├── development.md         # Development
├── contributing.md        # Contributing
└── advanced-usage.md      # Advanced usage
```

### Docs Standards

1. Chinese-English spacing
   - Space between Chinese and English words
   - Space between numbers and Chinese
   - Correct capitalization of proper nouns

2. Markdown rules
   - Standard Markdown syntax
   - Language specified for code blocks
   - Relative links

3. Content quality
   - Clear heading hierarchy
   - Practical code examples
   - Complete configuration explanations
   - FAQ

## 🎖️ Contributors

### Hall of Fame

Thanks to the following contributors:

- [@contributor1](https://github.com/contributor1) - Core developer
- [@contributor2](https://github.com/contributor2) - Docs maintainer
- [@contributor3](https://github.com/contributor3) - Testing expert

### Contribution Stats

```bash
# Contribution summary
git shortlog -sn

# Lines of code stats
cloc src/ tests/
```

### Become a Maintainer

Outstanding contributors may become maintainers:

Criteria:
- Continuous contributions for 3+ months
- High-quality code and documentation
- Active in community discussions
- Help other contributors

Permissions:
- Code review rights
- Manage Issues and PRs
- Release permissions
- Participate in technical decisions

## 📞 Contact

### Getting Help

1. GitHub Issues — bug reports and feature requests
2. GitHub Discussions — technical Q&A and discussions
3. Email — dev@your-company.com
4. Community group — [join link]

### Community Guidelines

We are committed to providing a friendly, safe, and welcoming environment for everyone, regardless of:
- Experience level
- Gender identity and expression
- Sexual orientation
- Disability
- Personal appearance
- Body size
- Race
- Ethnicity
- Age
- Religion

### Code of Conduct

Encouraged behaviors:
- Use friendly and inclusive language
- Respect differing views and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy toward other community members

Unacceptable behaviors:
- Sexualized language or imagery
- Trolling or personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other unethical or unprofessional conduct

## 🎉 Start Contributing

Ready to get started?

1. ⭐ Star this project
2. 🍴 Fork to your account
3. 🔧 Set up your dev environment
4. 💻 Start coding
5. 📝 Open your first PR

First-time ideas:
- Check the [Good First Issue](https://github.com/your-repo/claude-code-notifier/labels/good%20first%20issue) label
- Improve documentation
- Add tests
- Fix small bugs

Thank you for your contributions! Every contribution makes the project better. 🚀
