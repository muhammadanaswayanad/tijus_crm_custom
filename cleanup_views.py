import os
import shutil

def backup_and_cleanup_xml_files(directory):
    """Find duplicate or old XML files and create backups"""
    # Create a backup directory
    backup_dir = os.path.join(directory, 'backup_views')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Find all XML files
    xml_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml') and not file == 'crm_lead_views.xml':
                # Skip our main views file
                if 'backup_views' not in root:  # Don't process files in backup dir
                    full_path = os.path.join(root, file)
                    xml_files.append(full_path)
    
    # Move old XML files to backup
    for file_path in xml_files:
        if os.path.basename(os.path.dirname(file_path)) == 'views':
            # File is in views directory but not our main file
            backup_path = os.path.join(backup_dir, os.path.basename(file_path))
            print(f"Moving {file_path} to {backup_path}")
            shutil.copy2(file_path, backup_path)
            os.remove(file_path)

# Run the cleanup
cleanup_dir = "/home/tl/code/custom_addons/tijus_crm_custom"
backup_and_cleanup_xml_files(cleanup_dir)
print("Cleanup complete. Old XML files have been backed up.")
