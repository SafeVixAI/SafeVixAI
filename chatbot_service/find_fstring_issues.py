import ast, os, re

errors = []
for root, dirs, files in os.walk('tests'):
    for f in files:
        if not f.endswith('.py'):
            continue
        path = os.path.join(root, f)
        with open(path, 'r', encoding='utf-8') as fh:
            source = fh.read()
        try:
            compile(source, path, 'exec')
        except SyntaxError as e:
            errors.append((path, e.lineno, str(e)))

for p, l, m in errors:
    print(f'{p}:{l}: {m}')

print(f'Total files with syntax errors: {len(errors)}')
