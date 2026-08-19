from JSON_Tabs import json_tabs
from monitorLog import monitorLog
import time


def monitorLogWrapper(log_permissions, tabs, header, operation_report, log_file):
    
    #Writes a formatted log entry to the monitor log file.

    # if logging is disabled, do nothing
    if not log_permissions:
        return

    # build log line with or without header prefix
    if header:
        logtxt = f"{json_tabs(tabs)}{header}: {operation_report}"
    else:
        logtxt = f"{json_tabs(tabs)}{operation_report}"

    # append timestamp and write to log file
    monitorLog(logtxt + f" (Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')})", log_file)


def test_monitorLogWrapper():
    #Tests monitorLogWrapper with various combinations of inputs

    test_cases = [
        (True,  1, "Header1", "Operation1"),   # normal case with header
        (False, 2, "Header2", "Operation2"),   # logging disabled - should write nothing
        (True,  0, "",        "Operation3"),   # no header, no indent
        (True,  3, "Header4", ""),             # header but empty operation report
    ]

    for log_permissions, tabs, header, operation_report in test_cases:
        monitorLogWrapper(log_permissions, tabs, header, operation_report)
        print(f"Tested: log_permissions={log_permissions}, tabs={tabs}, header='{header}', operation_report='{operation_report}'")

if __name__ == "__main__":
    test_monitorLogWrapper()

