# Contributing to ROV AI Analyzer

Thank you for your interest in contributing!

## How to Contribute

### Reporting Bugs
1. Check existing issues first
2. Create new issue with:
   - Clear title
   - Steps to reproduce
   - Error messages
   - Your environment (OS, Python version)

### Suggesting Features
1. Open a discussion first
2. Describe the use case
3. Explain why it would help

### Pull Requests
1. Fork the repo
2. Create a feature branch
3. Make changes
4. Test locally
5. Submit PR with description

## Development Setup

```bash
git clone https://github.com/yourusername/rov-ai-analyzer.git
cd rov-ai-analyzer
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest black flake8
```

## Code Style
- Follow PEP 8
- Use Black for formatting: `black .`
- Use type hints where possible

## Testing
```bash
# Run tests
pytest

# Test specific file
pytest test_analyzer.py -v
```
