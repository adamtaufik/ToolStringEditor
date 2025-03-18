# 📖 User Manual – Deleum Tool String Editor

## 🏗️ Getting Started
1. **Launch the app**: Run `python main.py` (or open the `.exe` if packaged).
2. **Add tools**: Drag tools from the **Tool Library** to the **Drop Zone**.
3. **Edit tools**: Modify nominal size, OD, and connections.
4. **Save your configuration**: Use `Ctrl+S` or click "Save".
5. **Load configurations**: Use `Ctrl+O` or click "Load".
6. **Export**: Click "Export" to save as Excel or PDF.

## 🎨 UI Overview
- **Tool Library**: List of available tools.
- **Drop Zone**: Area where tools are placed.
- **Well Details**: Input for client, location, and well details.
- **Summary**: Automatically updates with OD, length, and weight.

## ⌨️ Keyboard Shortcuts
| Action          | Shortcut  |
|---------------|-----------|
| Save File    | `Ctrl+S`  |
| Load File    | `Ctrl+O`  |
| Export      | `Ctrl+E`  |
| Undo        | `Ctrl+Z`  |
| Redo        | `Ctrl+Y`  |

## 🛠️ Troubleshooting
- **Excel Export Fails**: Ensure **Microsoft Excel** is installed.
- **Missing Images**: Ensure the `assets/images/` folder exists.
- **App Crashes on Load**: Check that `tool_database.csv` is accessible.
