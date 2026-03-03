import ast, pathlib, sys

root = pathlib.Path('d:/Code/carevault-tensortitans/ml_service')
errors = 0
for f in sorted(root.rglob('*.py')):
    try:
        ast.parse(f.read_text(encoding='utf-8'))
        print('OK ', f.relative_to(root))
    except SyntaxError as e:
        print('ERR', f.relative_to(root), '->', e)
        errors += 1

sys.exit(errors)
