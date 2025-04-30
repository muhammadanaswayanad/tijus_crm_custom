#!/usr/bin/env python3
import os
import re
import shutil
from datetime import datetime

def backup_directory(dir_path):
    """Create a backup of the directory"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = os.path.join(os.path.dirname(dir_path), f"backup_{timestamp}")
    shutil.copytree(dir_path, backup_path)
    print(f"Created backup at: {backup_path}")
    return backup_path

def find_and_fix_problematic_xpath(directory):
    """Find and fix XML files with problematic XPath expressions"""
    problem_pattern = r"<xpath\s+expr=\"//button\[@name=['\"]action_view_sale_quotation['\"]\]"
    files_fixed = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    if re.search(problem_pattern, content):
                        # This file has the problematic pattern
                        new_content = re.sub(
                            r'(<xpath\s+expr=\"//button\[@name=[\'"]action_view_sale_quotation[\'"])\][^>]*>.*?</xpath>',
                            r'<!-- Removed problematic XPath: \1...]> -->',
                            content, 
                            flags=re.DOTALL
                        )
                        
                        with open(file_path, 'w') as f:
                            f.write(new_content)
                        
                        files_fixed.append(file_path)
                        print(f"Fixed file: {file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    return files_fixed

if __name__ == "__main__":
    module_path = "/home/tl/code/custom_addons/tijus_crm_custom"
    
    # First create a backup
    backup_path = backup_directory(module_path)
    
    # Find and fix problematic files
    fixed_files = find_and_fix_problematic_xpath(module_path)
    
    if fixed_files:
        print("\nFixed the following files:")
        for file in fixed_files:
            print(f"- {file}")
        print("\nPlease restart the Odoo server and upgrade your module.")
    else:
        print("\nNo files with problematic XPath expressions were found.")
        print("The issue might be in the database. Try uninstalling and reinstalling your module.")
    
    print(f"\nA backup of your module was created at: {backup_path}")
