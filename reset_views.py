#!/usr/bin/env python3
"""
This script should be run from the Odoo shell to reset problematic views.
To run:
1. Start Odoo shell:
   cd /opt/odoo/server-code
   ./odoo-bin shell -c /etc/odoo/odoo.conf -d your_database_name

2. Execute:
   exec(open('/home/tl/code/custom_addons/tijus_crm_custom/reset_views.py').read())
"""

# Find and delete problematic views
print("Searching for problematic views...")
problematic_views = env['ir.ui.view'].search([
    ('name', '=', 'crm.lead.form.custom'),
])

if problematic_views:
    print(f"Found {len(problematic_views)} problematic views. Deleting them...")
    problematic_views.unlink()
    print("Views deleted successfully.")
else:
    print("No problematic views found with the name 'crm.lead.form.custom'")

# Search for other views from this module
module_views = env['ir.ui.view'].search([
    ('name', 'like', 'tijus'),
])

if module_views:
    print(f"\nFound {len(module_views)} views from the tijus module:")
    for view in module_views:
        print(f"- {view.name} (id: {view.id}, model: {view.model})")
else:
    print("\nNo views found from the tijus module")

# Search specifically for views with sale_quotation in arch
print("\nSearching for views with 'action_view_sale_quotation' in their arch...")
quotation_views = env['ir.ui.view'].search([])
problematic_arch_views = []

for view in quotation_views:
    if view.arch and 'action_view_sale_quotation' in view.arch:
        problematic_arch_views.append(view)

if problematic_arch_views:
    print(f"Found {len(problematic_arch_views)} views with 'action_view_sale_quotation' in their arch:")
    for view in problematic_arch_views:
        print(f"- {view.name} (id: {view.id}, model: {view.model})")
        # Commenting out the auto-deletion to be safe
        # view.unlink()
    print("\nPlease review these views and delete them manually if needed")
else:
    print("No views found with 'action_view_sale_quotation' in their arch")

print("\nView cleanup process complete.")
env.cr.commit()
