# Troubleshooting Installation Issues

## ⚠️ MOST COMMON ISSUE: Virtual Environment Not Set Up

**If you get `ModuleNotFoundError` for Flask, dotenv, or any package:**

This means packages are installing to a different Python than you're running. **Solution: Use a virtual environment!**

### Quick Fix (Recommended for Everyone):

**Windows:**
```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it (IMPORTANT!)
venv\Scripts\activate

# You should see (venv) in your prompt now

# 3. Install requirements
pip install -r requirements-local.txt

# 4. Run the app
python local_app.py
```

**Mac/Linux:**
```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate it (IMPORTANT!)
source venv/bin/activate

# You should see (venv) in your prompt now

# 3. Install requirements
pip install -r requirements-local.txt

# 4. Run the app
python local_app.py
```

**To deactivate later:**
```bash
deactivate
```

---

## Common Issues

### 1. `ModuleNotFoundError: No module named 'flask'` (or any package)

**Problem:** Packages not installed in the Python environment you're running

**Solutions:**

**Option A: Use Virtual Environment (RECOMMENDED)**
```bash
# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements-local.txt
python local_app.py

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-local.txt
python local_app.py
```

**Option B: Check which Python/pip you're using**
```bash
# Check Python version and location
python --version
where python        # Windows
which python        # Mac/Linux

# Check pip location
where pip           # Windows
which pip           # Mac/Linux

# Use python -m pip to ensure same environment
python -m pip install -r requirements-local.txt
python local_app.py
```

**Option C: Install to user directory**
```bash
pip install -r requirements-local.txt --user
python local_app.py
```

### 2. `ModuleNotFoundError: No module named 'dotenv'`

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

### Windows:
```bash
# 1. Check Python version (needs 3.11+)
python --version

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements-local.txt

# 4. Set up configuration
copy config.example.yaml config.yaml
# Edit config.yaml with your information (use Notepad or VS Code)

# 5. Create .env file
echo ANTHROPIC_API_KEY=your_key_here > .env
# Or create manually with Notepad

# 6. Run the app
python local_app.py
```

### Mac/Linux:
```bash
# 1. Check Python version (needs 3.11+)
python3 --version

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements-local.txt

# 4. Set up configuration
cp config.example.yaml config.yaml
# Edit config.yaml with your information

# 5. Create .env file
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# 6. Run the app
python local_app.py
```

**After first setup, just:**
```bash
# Activate venv
venv\Scripts\activate    # Windows
source venv/bin/activate # Mac/Linux

# Run
python local_app.py
```

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
