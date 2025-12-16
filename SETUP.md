# Hammy the Hire Tracker - Setup Guide

## 🚀 Quick Start (Recommended)

### Option 1: Automated Setup (Easiest)

**Windows:**
```bash
# Double-click setup.bat or run in Command Prompt:
setup.bat
```

**Mac/Linux:**
```bash
# Run in Terminal:
chmod +x setup.sh
./setup.sh
```

The setup script automatically:
1. ✅ Creates a virtual environment
2. ✅ Installs all dependencies
3. ✅ Creates config.yaml from template
4. ✅ Creates .env file template

Then just:
1. Edit `config.yaml` with your information
2. Edit `.env` and add your `ANTHROPIC_API_KEY`
3. Run `python local_app.py`

---

### Option 2: Manual Setup

**Step-by-step for Windows:**

```bash
# 1. Check Python version (needs 3.11+)
python --version

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment (IMPORTANT!)
venv\Scripts\activate

# You should see (venv) in your prompt

# 4. Install dependencies
pip install -r requirements-local.txt

# 5. Set up configuration
copy config.example.yaml config.yaml
# Edit config.yaml with Notepad or VS Code

# 6. Create .env file
echo ANTHROPIC_API_KEY=your_key_here > .env
# Edit .env with Notepad and add your real API key

# 7. Run environment check
python check_env.py

# 8. Run the app!
python local_app.py
```

**Step-by-step for Mac/Linux:**

```bash
# 1. Check Python version (needs 3.11+)
python3 --version

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment (IMPORTANT!)
source venv/bin/activate

# You should see (venv) in your prompt

# 4. Install dependencies
pip install -r requirements-local.txt

# 5. Set up configuration
cp config.example.yaml config.yaml
# Edit config.yaml with nano or your preferred editor

# 6. Create .env file
echo "ANTHROPIC_API_KEY=your_key_here" > .env
# Edit .env and add your real API key

# 7. Run environment check
python check_env.py

# 8. Run the app!
python local_app.py
```

---

## 🔧 Validating Your Setup

Run the environment checker to verify everything is set up correctly:

```bash
python check_env.py
```

This will check:
- ✅ Python version (3.11+ required)
- ✅ Virtual environment (recommended)
- ✅ Required packages installed
- ✅ Configuration files exist
- ✅ API key is set

---

## 📝 Configuration

### 1. Edit config.yaml

Required sections:

```yaml
user:
  name: "Your Name"
  email: "your.email@example.com"
  # ... other fields

resumes:
  files:
    - "resumes/fullstack_developer_resume.txt"
    # Add your resume files

preferences:
  locations:
    primary:
      - name: "Remote"
        type: "remote"
      # Add your location preferences
```

See [config.example.yaml](config.example.yaml) for full details.

### 2. Set up your resumes

```bash
# Copy templates
cp resumes/templates/fullstack_developer_resume_template.txt resumes/fullstack_developer_resume.txt

# Edit with your information
# Remove all [PLACEHOLDER] text
```

See [resumes/README.md](resumes/README.md) for details.

### 3. Get your Anthropic API key

1. Sign up at https://console.anthropic.com/
2. Go to API Keys section
3. Create a new API key
4. Add to your `.env` file:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 4. Set up Gmail OAuth (Optional but recommended)

Follow the guide in [README.md](README.md#gmail-setup) to:
1. Create Google Cloud project
2. Enable Gmail API
3. Download credentials.json
4. Run first OAuth flow

---

## 🐋 Docker Setup (Alternative)

If you prefer Docker:

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Access at http://localhost:5000
```

See [DOCKER.md](DOCKER.md) for full Docker setup guide.

---

## ⚠️ Common Issues

### "ModuleNotFoundError: No module named 'flask'"

**Solution:** You're not in the virtual environment or packages aren't installed.

```bash
# Activate virtual environment first
venv\Scripts\activate    # Windows
source venv/bin/activate # Mac/Linux

# Then install
pip install -r requirements-local.txt
```

### "ModuleNotFoundError: No module named 'dotenv'"

**Solution:** Wrong package installed.

```bash
pip uninstall dotenv
pip install python-dotenv
```

### "Configuration Error: Config file not found"

**Solution:** Create config.yaml from template.

```bash
# Windows
copy config.example.yaml config.yaml

# Mac/Linux
cp config.example.yaml config.yaml
```

### "ANTHROPIC_API_KEY not set"

**Solution:** Create or edit .env file.

```bash
# Create .env with your key
echo ANTHROPIC_API_KEY=your_key_here > .env
```

**For more issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

---

## 🎯 Next Steps After Setup

1. **Run the app:** `python local_app.py`
2. **Open dashboard:** http://localhost:5000
3. **Scan emails:** Click "📧 Scan Gmail" button
4. **Analyze jobs:** Click "🤖 Analyze All" button
5. **Install Chrome extension:** See extension/README.md

---

## 📚 Additional Resources

- [README.md](README.md) - Full documentation
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [DOCKER.md](DOCKER.md) - Docker deployment guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contributing guidelines (coming soon)
- [ROADMAP.md](ROADMAP.md) - Future plans and features

---

## 💡 Tips

**Always activate the virtual environment before running:**
```bash
venv\Scripts\activate    # Windows
source venv/bin/activate # Mac/Linux
```

**To deactivate when done:**
```bash
deactivate
```

**Check if virtual environment is active:**
- You should see `(venv)` at the start of your command prompt

**Update dependencies:**
```bash
pip install -r requirements-local.txt --upgrade
```

---

## 🆘 Need Help?

1. Run `python check_env.py` to diagnose issues
2. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Open an issue on GitHub
4. Check GitHub Discussions for Q&A

---

**Ready to go HAM on your job search!** 🐷🚀
