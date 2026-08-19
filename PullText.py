import os
from datetime import datetime


def write_misc_files(output_path, json_body):
    pull_tablet_info(output_path, json_body.get("tablet_data"))
    pull_disk_info(output_path, json_body.get("disk_data"))
    pull_custom_info(output_path, json_body.get("custom_data"))
    pull_quality_info(output_path, json_body.get("quality_data"))
    pull_block_info(output_path, json_body.get("block_data"))
    pull_notes_info(output_path, json_body.get("notes_data"))

def pull_tablet_info(folder_path, data):
    if data is None:
        return
    tablet_path = os.path.join(folder_path, "TABLET SPECS.TXT")
    with open(tablet_path, "w") as f:
        f.write(data)

def pull_disk_info(folder_path, data):
    if data is None:
        return
    disk_path = os.path.join(folder_path, "DISK_FREE.TXT")
    with open(disk_path, "w") as f:
        f.write(data)

def pull_custom_info(folder_path, data):
    if data is None:
        return
    custom_path = os.path.join(folder_path, "CUSTOM CONDITION.TXT")
    with open(custom_path, "w") as f:
        f.write(data)

def pull_quality_info(folder_path, data):
    if data is None:
        return
    quality_path = os.path.join(folder_path, "QUALITYOFF.TXT")
    with open(quality_path, "w") as f:
        f.write(data)

def pull_block_info(folder_path, data):
    if data is None:
        return
    block_path = os.path.join(folder_path, "vsc_blockChainLog.TXT")
    entry = f"     Pulling Files: Bearing Files were Succesfully Pulled from Arca @local time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    data += entry
    with open(block_path, "w") as f:
        f.write(data)

def pull_notes_info(folder_path, data):
    if data is None:
        return
    notes_path = os.path.join(folder_path, f"{os.path.basename(folder_path)}_NOTES.TXT")
    with open(notes_path, "w") as f:
        f.write(data)