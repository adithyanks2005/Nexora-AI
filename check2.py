import urllib.request
html = urllib.request.urlopen('https://nexora-ai-flax.vercel.app/').read().decode('utf-8', errors='replace')

# Check guest button
idx = html.find('Continue as Guest')
if idx != -1:
    print('GUEST BUTTON CONTEXT:')
    print(repr(html[max(0,idx-250):idx+60]))
    print()

# Check Google button
idx2 = html.find('Continue with Google')
if idx2 != -1:
    print('GOOGLE BUTTON CONTEXT:')
    print(repr(html[max(0,idx2-400):idx2+60]))
    print()

# Check if function definitions exist
funcs = ['function continueAsGuest', 'function openGoogleOAuthPopup', 'function showLoginScreen', 'function checkAuth']
for f in funcs:
    print(f'{f}: {"FOUND" if f in html else "MISSING"}')
