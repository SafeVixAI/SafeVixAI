import os, re

# Search for f-strings with backslash inside {} in .py files
pattern = r"""f['\"].*\{[^}]*\\[ntr\\][^}]*\}"""
source_dirs = ['.']

for sd in source_dirs:
    for root, dirs, files in os.walk(sd):
        # Skip venv, __pycache__, .git
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.venv', '.git', 'node_modules', '.mypy_cache', '.pytest_cache')]
        for f in files:
            if not f.endswith('.py'):
                continue
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
            # Simple check: f-string with backslash
            for i, line in enumerate(content.split('\n'), 1):
                in_fstring = False
                in_brace = False
                brace_depth = 0
                for j, ch in enumerate(line):
                    if ch in ('f', 'F') and j+1 < len(line) and line[j+1] in ('"', "'"):
                        in_fstring = True
                    if in_fstring and ch == '{':
                        in_brace = True
                        brace_depth += 1
                    elif in_fstring and ch == '}':
                        brace_depth -= 1
                        if brace_depth <= 0:
                            in_brace = False
                            in_fstring = False
                    if in_brace and ch == '\\':
                        print(f'{path}:{i}:{j}: {line.strip()[:100]}')
                        break
