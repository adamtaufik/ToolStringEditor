from datetime import datetime, timedelta

# Use known reference from SmartView
REFERENCE_TIMESTAMP = 739435.8148
REFERENCE_DATETIME = datetime(2025, 7, 3, 22, 38, 1)

def smartview_timestamp_to_datetime(timestamp):
    delta_days = timestamp - REFERENCE_TIMESTAMP
    delta = timedelta(days=delta_days)
    return REFERENCE_DATETIME + delta
def format_smartview_time(timestamp):
    dt = smartview_timestamp_to_datetime(timestamp)
    return dt.strftime('%d/%m/%Y  %H:%M:%S')

print(format_smartview_time(739435.81480000))  # 06/07/2025  11:10:01
