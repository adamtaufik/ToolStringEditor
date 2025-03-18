# 🛠️ Installation Guide

This guide walks you through setting up **Deleum Tool String Editor**.

## 📋 Requirements
- **Windows 10/11**
- **Python 3.10+**
- **pip** (Python package manager)
- **Microsoft Excel** (for exporting PDFs)

## 📦 Installing Dependencies
1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/Deleum-TS-Editor.git
   cd Deleum-TS-Editor
   ```
2. **Create a virtual environment (optional but recommended):**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Mac/Linux
   venv\Scripts\activate  # On Windows
   ```
3. **Install required Python packages:**
   ```sh
   pip install -r requirements.txt
   ```

## 🚀 Running the Application
Run the software with:
```sh
python main.py
```

## 📦 Creating an Executable (Optional)
To package the application as an EXE:
```sh
pyinstaller --noconsole --onefile --add-data "assets;assets" main.py
```
This will generate a `.exe` file in the **dist/** folder.

## 🔄 Updating the Application
To update, pull the latest changes and reinstall dependencies:
```sh
git pull origin main
pip install -r requirements.txt --upgrade
```
