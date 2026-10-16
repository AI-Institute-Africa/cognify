import os
import re

base_dir = r"c:\Users\USER 2\Downloads\project1\project1\land_registry"

def rebrand_files():
    for root, dirs, files in os.walk(base_dir):
        # skip virtual envs, git, __pycache__, etc
        if any(ignored in root for ignored in ['.git', '__pycache__', 'venv', 'env', 'migrations', '.gemini']):
            continue

        for file in files:
            if file.endswith('.py') or file.endswith('.html') or file.endswith('.md'):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Match Records Intelligence or Records Intelligence
                    # The user said replace Records Intelligence -> Records Intelligence
                    new_content = content.replace("Records Intelligence", "Records Intelligence")
                    new_content = new_content.replace("Records Intelligence", "Records Intelligence")
                    
                    if content != new_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Updated {filepath}")
                except Exception as e:
                    pass

if __name__ == '__main__':
    rebrand_files()
    print("Rebranding to Records Intelligence complete.")
