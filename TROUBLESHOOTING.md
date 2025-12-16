# Troubleshooting Installation Issues

## Common Issues

### 1. `ModuleNotFoundError: No module named 'dotenv'`

**Problem:** You installed the wrong package. There are two packages:
- ❌ `dotenv` (0.9.9) - Wrong package
- ✅ `python-dotenv` (1.0.0+) - Correct package

**Solution:**

```bash
# Uninstall the wrong package
pip uninstall dotenv

# Install the correct package
pip install python-dotenv

# Or install all requirements at once
pip install -r requirements-local.txt
```

### 2. Module Import Errors on Windows

**Problem:** Python can't find installed modules

**Solution:**
```bash
# Make sure you're using the correct Python
python --version

# Reinstall all requirements
pip install -r requirements-local.txt --force-reinstall

# Or use python -m pip
python -m pip install -r requirements-local.txt
```

### 3. Virtual Environment Issues

**Recommended:** Always use a virtual environment

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate

# Install requirements
pip install -r requirements-local.txt
```

### 4. Permission Errors

**Windows:**
```bash
# Run as administrator or use --user flag
pip install -r requirements-local.txt --user
```

**Mac/Linux:**
```bash
pip install -r requirements-local.txt --user
```

### 5. Conflicting Package Versions

**Solution:**
```bash
# Clean install
pip uninstall -y -r requirements-local.txt
pip install -r requirements-local.txt
```

## Quick Start Checklist

1. ✅ Python 3.11+ installed (`python --version`)
2. ✅ Virtual environment created and activated
3. ✅ Install requirements: `pip install -r requirements-local.txt`
4. ✅ Copy config: `cp config.example.yaml config.yaml`
5. ✅ Edit config.yaml with your information
6. ✅ Set API key: `echo "ANTHROPIC_API_KEY=your_key" > .env`
7. ✅ Run: `python local_app.py`

## Still Having Issues?

1. Check Python version: `python --version` (needs 3.11+)
2. Check pip version: `pip --version`
3. Try clean reinstall: `pip install -r requirements-local.txt --force-reinstall`
4. Check for conflicting packages: `pip list | grep dotenv`
5. Open an issue on GitHub with your error message

## Platform-Specific Notes

### Windows
- Use `venv\Scripts\activate` to activate virtual environment
- May need to run PowerShell as administrator
- Use forward slashes in paths or double backslashes

### macOS
- May need to use `python3` and `pip3` commands
- Install Python from python.org (not system Python)

### Linux
- Install python3-venv: `sudo apt install python3-venv`
- Use `python3` and `pip3` commands
