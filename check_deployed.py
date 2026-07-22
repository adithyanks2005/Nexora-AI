import urllib.request
import re

r = urllib.request.urlopen('https://nexora-ai-henna-five.vercel.app/')
html = r.read().decode('utf-8', errors='replace')

print("=== DEPLOYED FRONTEND CHECK ===\n")

# 1. Check .app default display
app_match = re.search(r'\.app\{display:([^;}]+)', html)
if app_match:
    print(f"✓ .app default display: {app_match.group(1)}")
else:
    print("✗ .app CSS not found")

# 2. Check loginScreen display
login_match = re.search(r'#loginScreen\{[^}]*display:([^;}]+)', html)
if login_match:
    print(f"✓ #loginScreen display: {login_match.group(1)}")
else:
    print("✗ #loginScreen CSS not found")

# 3. GOOGLE_CLIENT_ID
gid = re.search(r"const GOOGLE_CLIENT_ID = '([^']+)'", html)
if gid:
    cid = gid.group(1)
    print(f"✓ GOOGLE_CLIENT_ID: {cid[:40]}...")
else:
    print("✗ GOOGLE_CLIENT_ID not found")

# 4. checkAuth at parse time
if 'checkAuth();' in html and 'document.querySelector' in html:
    # Find the exact line
    lines = html.split('\n')
    for i, line in enumerate(lines):
        if 'checkAuth();' in line and '//' not in line.split('checkAuth()')[0]:
            print(f"✓ checkAuth() called at line {i}")
            break
else:
    print("✗ checkAuth() not called at parse time")

# 5. Service worker registration
if 'serviceWorker' in html and 'service-worker.js' in html:
    print("✓ Service worker registered")
else:
    print("✗ Service worker NOT registered")

# 6. authFetch 401 handling
if 'res.status === 401' in html:
    print("✓ authFetch has 401 handler")
else:
    print("✗ authFetch missing 401 handler")

# 7. BMI height label ID
if 'id="bmi-hlabel"' in html:
    print("✓ BMI height label has ID")
else:
    print("✗ BMI height label missing ID")

print(f"\nHTML size: {len(html)} chars")
print(f"Script blocks: {html.count('<script>')}")
