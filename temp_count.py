import os
count = 0
skip = {'__pycache__', '.git', '.venv', 'node_modules'}
exts = {'.py', '.html', '.css', '.js', '.json', '.md', '.txt', '.yaml', '.yml', '.toml', '.ini'}
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in skip]
    for f in files:
        if os.path.splitext(f)[1].lower() in exts:
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as fh:
                    count += sum(1 for _ in fh)
            except Exception:
                pass
print(count)
