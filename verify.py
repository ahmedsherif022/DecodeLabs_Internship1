import json, os

# Check JSON
size = os.path.getsize('student_advisor_data.json') / 1024
with open('student_advisor_data.json', encoding='utf-8') as f:
    data = json.load(f)

roles = data['role_profiles']
print(f'student_advisor_data.json => {size:.1f} KB')
print(f'Roles built: {len(roles)}')
print()
print(f"{'Role':<35} {'n':>6}  {'Salary':>10}  {'Exp':>5}  Top-3 Languages")
print('-' * 90)
for role, p in roles.items():
    sal = p['salary'].get('median_usd', 'N/A')
    exp = p['experience'].get('median_years', 'N/A')
    langs = [x['name'] for x in p['languages'][:3]]
    sal_str = f"${sal:,}" if isinstance(sal, int) else str(sal)
    print(f"  {role:<33} {p['sample_count']:>6,}  {sal_str:>10}  {str(exp):>5}  {langs}")

print()
print('Files in project:')
for f in os.listdir('.'):
    size_b = os.path.getsize(f)
    print(f"  {f:<45} {size_b/1024:>8.1f} KB")
