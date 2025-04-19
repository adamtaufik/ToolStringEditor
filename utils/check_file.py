import os


def is_file_open(file_path):
    """Check if the specific Excel file is open."""
    try:
        import win32com.client
        excel = win32com.client.Dispatch("Excel.Application")
        for wb in excel.Workbooks:
            if os.path.abspath(wb.FullName) == os.path.abspath(file_path):
                return True  # File is open
    except Exception as e:
        print(f"⚠️ Could not check file status: {e}")
    return False