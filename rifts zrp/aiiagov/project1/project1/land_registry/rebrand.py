import os
import re

TEMPLATE_DIR = r"c:\Users\USER 2\Downloads\project1\project1\land_registry\registry\templates"
# Also do Python files if any? The prompt mentioned "all instances of Registry" etc. in the system.
# The user's grep search showed mostly templates.
# I'll include .html and .py but exclude rebrand.py itself, and migrations.
BASE_DIR = r"c:\Users\USER 2\Downloads\project1\project1\land_registry"

replacements = [
    (r"Authored by Institutional Governance Services", "Authored and powered by AI Institute Africa"),
    (r"LAND REGISTRY", "STRATEGIC INTELLIGENCE PLATFORM"),
    (r"Land Registry", "Strategic Intelligence Platform"),
    (r"land registry", "strategic intelligence platform"),
    (r"Lands", "Records Intelligence"),
    (r"lands", "afc bank"),
    (r"Land", "Records Intelligence"),
    (r"land ", "afc bank "), # be careful with 'land' as it could be part of a word.
    (r"Registry", "Records Intelligence"),
    (r"registry", "Records Intelligence"),
]

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    # For 'land', to avoid replacing in 'landscape' or 'island', we can use word boundaries
    new_content = re.sub(r'Authored by Institutional Governance Services', 'Authored and powered by AI Institute Africa', new_content, flags=re.IGNORECASE)
    
    new_content = re.sub(r'\bLAND REGISTRY\b', 'STRATEGIC INTELLIGENCE PLATFORM', new_content)
    new_content = re.sub(r'\bLand Registry\b', 'Strategic Intelligence Platform', new_content)
    new_content = re.sub(r'\bland registry\b', 'strategic intelligence platform', new_content)
    
    new_content = re.sub(r'\bLands\b', 'Records Intelligence', new_content)
    new_content = re.sub(r'\blands\b', 'afc bank', new_content)
    new_content = re.sub(r'\bLand\b', 'Records Intelligence', new_content)
    new_content = re.sub(r'\bland\b', 'afc bank', new_content)
    
    # We should avoid replacing 'registry' inside 'land_registry' or URL paths like 'registry/'
    # Since 'land_registry' is the app name, changing "registry" -> "Records Intelligence" in URL patterns 
    # or import statements will break the python code!
    # So we should ONLY do these replacements in HTML templates, and maybe carefully in py files without breaking imports.
    # To be safe, let's focus on HTML template texts and forms.py labels.
    pass

def process_templates():
    modified_count = 0
    for root, dirs, files in os.walk(TEMPLATE_DIR):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                new_content = re.sub(r'Authored by Institutional Governance Services', 'Authored and powered by AI Institute Africa', new_content, flags=re.IGNORECASE)
                
                new_content = re.sub(r'\bLAND REGISTRY\b', 'STRATEGIC INTELLIGENCE PLATFORM', new_content)
                new_content = re.sub(r'\bLand Registry\b', 'Strategic Intelligence Platform', new_content)
                new_content = re.sub(r'\bland registry\b', 'strategic intelligence platform', new_content)
                
                new_content = re.sub(r'\bLands\b', 'Records Intelligence', new_content)
                new_content = re.sub(r'\blands\b', 'afc bank', new_content)
                new_content = re.sub(r'\bLand\b', 'Records Intelligence', new_content)
                new_content = re.sub(r'\bland\b', 'afc bank', new_content)
                
                # 'Registry' and 'registry' -> 'Records Intelligence'
                # but NOT inside {% url '...' %} or href="/registry/..."
                # A simple regex for text not in tags might be too complex, but we can just replace
                # Registry and registry. In django templates, we usually have 'registry' in app labels.
                # Let's use a targeted replace for " Registry" or ">Registry" or "Registry "
                # Actually, replacing 'Registry' (capital R) is usually safe for UI labels.
                new_content = re.sub(r'\bRegistry\b', 'Records Intelligence', new_content)
                
                # For lowercase 'registry', we only replace if it's not part of a URL or static tag
                # We can skip lowercase registry or do it carefully. Let's just do lowercase 'registry ' (with space) 
                # or ' registry ' to be safe.
                new_content = re.sub(r'(?<!_)registry(?=[ \.,])', 'Records Intelligence', new_content)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    modified_count += 1
    print(f"Modified {modified_count} HTML files in {TEMPLATE_DIR}")

process_templates()
