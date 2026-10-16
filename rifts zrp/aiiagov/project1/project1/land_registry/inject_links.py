import os

filepath = r"c:\Users\USER 2\Downloads\project1\project1\land_registry\registry\services\governance.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the closing signatures with the injected System URL
replacements = [
    (
        "\\n\\nBest regards,\\nRIFTS-X Governance\"",
        "\\n\\nSystem URL: http://127.0.0.1:8000\\n\\nBest regards,\\nRIFTS-X Governance\""
    ),
    (
        "\\n        Best regards,\\n        Registry Governance System",
        "\\n\\n        System URL: http://127.0.0.1:8000\\n        Best regards,\\n        Registry Governance System"
    ),
    (
        "\\n        Best regards,\\n        Strategic Intelligence Platform Governance",
        "\\n\\n        System URL: http://127.0.0.1:8000\\n        Best regards,\\n        Strategic Intelligence Platform Governance"
    )
]

new_content = content
for old, new in replacements:
    new_content = new_content.replace(old, new)

if new_content != content:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Injected system URL into governance.py email bodies.")
else:
    print("No changes made. Patterns might not match.")
