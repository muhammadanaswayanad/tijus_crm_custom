import os

def find_xpath_in_files(directory, text_to_find):
    """Find files containing specific text in a directory"""
    found_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                        if text_to_find in content:
                            found_files.append(full_path)
                            print(f"Found in: {full_path}")
                except Exception as e:
                    print(f"Error reading {full_path}: {e}")
    
    return found_files

# Search for the problematic xpath
search_dir = "/home/tl/code/custom_addons/tijus_crm_custom"
problematic_text = "action_view_sale_quotation"
found = find_xpath_in_files(search_dir, problematic_text)

if not found:
    print("No files found with the problematic XPath. There might be other issues.")
else:
    print(f"\nFound {len(found)} files with the problematic XPath.")
    for file in found:
        print(f"- {file}")
