import sys
sys.path.insert(0, '.')

# Test 1: Groq API
try:
    import os
    from groq import Groq
    c = Groq(api_key=os.environ.get("GROQ_API_KEY", "your-api-key-here"))
    r = c.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "say ok"}],
        max_tokens=5
    )
    print("GROQ OK:", r.choices[0].message.content)
except Exception as e:
    print("GROQ ERROR:", type(e).__name__, str(e))

# Test 2: Firebase Admin token verification setup
try:
    import firebase_admin
    from firebase_admin import credentials, auth
    cred = credentials.Certificate("./serviceAccount.json")
    try:
        app = firebase_admin.initialize_app(cred)
    except ValueError:
        app = firebase_admin.get_app()
    print("FIREBASE ADMIN OK: app initialized, project =", app.project_id)
except Exception as e:
    print("FIREBASE ADMIN ERROR:", type(e).__name__, str(e))
