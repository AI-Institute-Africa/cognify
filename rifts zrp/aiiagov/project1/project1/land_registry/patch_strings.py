import os

views_path = r"c:\Users\USER 2\Downloads\project1\project1\land_registry\registry\views.py"
with open(views_path, 'r', encoding='utf-8') as f:
    views_content = f.read()

# Replace 'Review' with 'Awaiting Project Leader Approval' for phase statuses
views_content = views_content.replace(
    "status='Review'", "status='Awaiting Project Leader Approval'"
)
views_content = views_content.replace(
    "status__in=['Review'", "status__in=['Awaiting Project Leader Approval'"
)

with open(views_path, 'w', encoding='utf-8') as f:
    f.write(views_content)

print(f"Patched statuses in {views_path}")

# Now patch any templates that might have 'Review' -> 'Awaiting Project Leader Approval'
templates_dir = r"c:\Users\USER 2\Downloads\project1\project1\land_registry\registry\templates"
for root, dirs, files in os.walk(templates_dir):
    for filename in files:
        if filename.endswith(".html"):
            filepath = os.path.join(root, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content.replace("phase.status == 'Review'", "phase.status == 'Awaiting Project Leader Approval'")
            new_content = new_content.replace("status == 'Review'", "status == 'Awaiting Project Leader Approval'")
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Patched statuses in {filepath}")

