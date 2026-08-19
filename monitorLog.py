
import os

# log file will be created in the same directory as this script
LOG_FILE = os.path.join(os.path.dirname(__file__), "monitorLog.txt")


def monitorLog(logtxt, log_file):
    
    #Appends a single line of text to the monitor log file.
    #Called by monitorLogWrapper which handles formatting and timestamps.

    try:
        with open(log_file, "a") as f:
            f.write(logtxt + "\n")
    except Exception as e:
        print(f"Error occurred while writing to monitor log: {e}")


def test_monitorLog():
    #Writes several test entries to the log file and confirms no errors
    test_cases = [
        "Test log entry 1",
        "Test log entry 2",
        "Test log entry 3",
    ]

    for logtxt in test_cases:
        monitorLog(logtxt)
        print(f"Logged: {logtxt}")

    print(f"\nCheck {LOG_FILE} to verify entries were written.")

