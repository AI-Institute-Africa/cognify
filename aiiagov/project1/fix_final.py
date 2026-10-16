import os

def fix_file(path, old, new):
    if not os.path.exists(path):
        print(f"Error: {path} not found")
        return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if old in content:
        new_content = content.replace(old, new)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new_content)
        print(f"Successfully fixed {os.path.basename(path)}")
    else:
        print(f"Target pattern not found in {os.path.basename(path)}")

# Fix files.html
files_path = r'c:\Users\USER 2\Downloads\project1\project1\land_registry\registry\templates\files.html'
fix_file(files_path, 'handler|add:0==u.id', 'handler|add:0 == u.id')
fix_file(files_path, 'department|add:0==d.id', 'department|add:0 == d.id')

# Fix executive_dashboard.html
dash_path = r'c:\Users\USER 2\Downloads\project1\project1\land_registry\registry\templates\executive_dashboard.html'
# Using a broader match for the dashboard split tag
import re
with open(dash_path, 'r', encoding='utf-8') as f:
    dash_content = f.read()

# Pattern for the split location_heatmap tag
pattern = r'\{\{\s*location_heatmap\|\s*safe\s*\}\}'
# But in our case it was split by newline: {{ location_heatmap| safe\n    }}
# So let's use a regex that handles whitespace and newlines
regex_pattern = r'\{\{\s*location_heatmap\s*\|\s*safe\s*(\n\s*)?\}\}'
if re.search(regex_pattern, dash_content):
    new_dash_content = re.sub(regex_pattern, '{{ location_heatmap|safe }}', dash_content)
    # Also fix the trailing semicolon if it was on next line or missing
    new_dash_content = new_dash_content.replace('{{ location_heatmap|safe }}\n    }};', '{{ location_heatmap|safe }};')
    with open(dash_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(new_dash_content)
    print("Successfully fixed executive_dashboard.html")
else:
    print("Pattern not found in executive_dashboard.html")
