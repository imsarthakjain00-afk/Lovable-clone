from src.utils.settings import settings

def get_firebase_snippet() -> str:
    """Returns a script snippet containing Firebase configuration if available."""
    if not settings.FIREBASE_API_KEY:
        return ""
    
    return f"""
<!-- Firebase Authentication & Firestore Config -->
<script type="module">
  import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
  import {{ getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut }} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";
  import {{ getFirestore, collection, addDoc, getDocs, query, where }} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

  const firebaseConfig = {{
    apiKey: "{settings.FIREBASE_API_KEY}",
    authDomain: "{settings.FIREBASE_AUTH_DOMAIN}",
    projectId: "{settings.FIREBASE_PROJECT_ID}",
    storageBucket: "{settings.FIREBASE_STORAGE_BUCKET}",
    messagingSenderId: "{settings.FIREBASE_MESSAGING_SENDER_ID}",
    appId: "{settings.FIREBASE_APP_ID}"
  }};

  // Initialize Firebase
  const app = initializeApp(firebaseConfig);
  const auth = getAuth(app);
  const db = getFirestore(app);

  // Expose to window for the generated inline scripts to use
  window.firebaseAuth = auth;
  window.firebaseDb = db;
  window.firebaseSignIn = signInWithEmailAndPassword;
  window.firebaseSignUp = createUserWithEmailAndPassword;
  window.firebaseSignOut = signOut;
</script>
"""

def inject_firebase(html_content: str) -> str:
    """Injects the Firebase SDK and configuration into the generated HTML `<head>`."""
    snippet = get_firebase_snippet()
    if not snippet:
        return html_content
    
    # Simple insertion before </head>
    if "</head>" in html_content:
        return html_content.replace("</head>", f"{snippet}\n</head>")
    return html_content
