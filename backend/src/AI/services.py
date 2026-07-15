from src.utils.settings import settings
import json
import logging
from src.AI.agent import WebsiteCreationAgent

logger = logging.getLogger(__name__)


def _build_firebase_auth_script(project_id: int) -> str:
    """
    Returns a self-contained <script> block that:
      1. Initialises Firebase Auth (Google + Email/Password)
      2. On sign-in, stores the user profile in Supabase (website_users table)
      3. Exposes window helpers: signInWithGoogle(), signInWithEmail(),
         signUpWithEmail(), signOutUser(), getCurrentUser()
    Uses the compat CDN build so it works in plain HTML with no bundler.
    """
    firebase_config = json.dumps({
        "apiKey":            settings.FIREBASE_API_KEY            or "",
        "authDomain":        settings.FIREBASE_AUTH_DOMAIN        or "",
        "projectId":         settings.FIREBASE_PROJECT_ID         or "",
        "storageBucket":     settings.FIREBASE_STORAGE_BUCKET     or "",
        "messagingSenderId": settings.FIREBASE_MESSAGING_SENDER_ID or "",
        "appId":             settings.FIREBASE_APP_ID             or "",
        "measurementId":     settings.FIREBASE_MEASUREMENT_ID     or "",
    })

    supabase_url  = settings.SUPABASE_URL      or ""
    supabase_key  = settings.SUPABASE_ANON_KEY or ""

    return f"""
<!-- ═══════════════════════════════════════════════════════════════
     Firebase Auth + Supabase (injected by Lovable Clone)
     Auth provider : Firebase  |  Data store : Supabase
═══════════════════════════════════════════════════════════════ -->
<script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/9.23.0/firebase-auth-compat.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
(function() {{
  // ── Firebase init ──────────────────────────────────────────────
  const _fbConfig = {firebase_config};
  if (!firebase.apps.length) {{
    firebase.initializeApp(_fbConfig);
  }}
  const _auth = firebase.auth();

  // ── Supabase init ──────────────────────────────────────────────
  const _sb = supabase.createClient("{supabase_url}", "{supabase_key}");
  window.supabaseDb  = _sb;   // also expose for page scripts
  window.projectSiteId = "{project_id}";

  // ── Save / update user profile in Supabase after login ────────
  async function _syncUserToSupabase(fbUser) {{
    if (!fbUser) return;
    try {{
      await _sb.from("website_users").upsert({{
        firebase_uid : fbUser.uid,
        email        : fbUser.email || "",
        display_name : fbUser.displayName || "",
        photo_url    : fbUser.photoURL  || "",
        project_id   : "{project_id}",
        last_login   : new Date().toISOString()
      }}, {{ onConflict: "firebase_uid,project_id" }});
    }} catch(e) {{
      console.warn("[Auth] Supabase sync error:", e.message);
    }}
  }}

  // ── Auth state listener ────────────────────────────────────────
  _auth.onAuthStateChanged(function(user) {{
    window._currentFirebaseUser = user || null;
    if (user) {{
      _syncUserToSupabase(user);
      // Dispatch event so page scripts can react
      document.dispatchEvent(new CustomEvent("userSignedIn",  {{ detail: user }}));
    }} else {{
      document.dispatchEvent(new CustomEvent("userSignedOut", {{ detail: null  }}));
    }}
  }});

  // ── Public helpers ─────────────────────────────────────────────

  /** Sign in with Google popup */
  window.signInWithGoogle = async function() {{
    const provider = new firebase.auth.GoogleAuthProvider();
    try {{
      const result = await _auth.signInWithPopup(provider);
      return result.user;
    }} catch(e) {{
      console.error("[Auth] Google sign-in failed:", e.message);
      throw e;
    }}
  }};

  /** Sign in with email + password */
  window.signInWithEmail = async function(email, password) {{
    try {{
      const result = await _auth.signInWithEmailAndPassword(email, password);
      return result.user;
    }} catch(e) {{
      console.error("[Auth] Email sign-in failed:", e.message);
      throw e;
    }}
  }};

  /** Create account with email + password */
  window.signUpWithEmail = async function(email, password, displayName) {{
    try {{
      const result = await _auth.createUserWithEmailAndPassword(email, password);
      if (displayName) {{
        await result.user.updateProfile({{ displayName }});
      }}
      return result.user;
    }} catch(e) {{
      console.error("[Auth] Sign-up failed:", e.message);
      throw e;
    }}
  }};

  /** Sign out */
  window.signOutUser = async function() {{
    await _auth.signOut();
  }};

  /** Get currently signed-in user (null if not signed in) */
  window.getCurrentUser = function() {{
    return window._currentFirebaseUser || null;
  }};

  console.log("[Lovable] Firebase Auth ready. Use: signInWithGoogle(), signInWithEmail(), signUpWithEmail(), signOutUser()");
}})();
</script>
"""


def inject_auth_into_html(html_content: str, project_id: int) -> str:
    """
    Injects the Firebase Auth + Supabase block just before </head>.
    Falls back gracefully if Firebase config is not yet set.
    """
    if not html_content:
        return ""

    if not settings.FIREBASE_API_KEY:
        # Firebase not configured — inject only Supabase client
        logger.warning("[inject_auth] FIREBASE_API_KEY not set — injecting Supabase only")
        script = f"""
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
<script>
  window.supabaseDb = supabase.createClient("{settings.SUPABASE_URL or ''}", "{settings.SUPABASE_ANON_KEY or ''}");
  window.projectSiteId = "{project_id}";
</script>
"""
    else:
        script = _build_firebase_auth_script(project_id)

    head_end = html_content.lower().find("</head>")
    if head_end != -1:
        return html_content[:head_end] + script + html_content[head_end:]
    return script + html_content


# Keep legacy name so nothing else breaks
def inject_supabase_to_html(html_content: str, project_id: int) -> str:
    return inject_auth_into_html(html_content, project_id)


async def process_user_prompt(
    project_id: int,
    user_prompt: str,
    current_state: str,
    current_brain: dict,
    current_manifest: dict,
    current_code: str = None,
    images: list = None,
) -> dict:
    """
    Instantiates the stateful WebsiteCreationAgent and processes the user's message.
    """
    agent = WebsiteCreationAgent(
        project_id=project_id,
        initial_state=current_state,
        initial_brain=current_brain,
        initial_manifest=current_manifest
    )

    response_data = await agent.process_message(user_prompt, current_code)

    # Inject Firebase Auth + Supabase into generated HTML
    if response_data.get("generated_code"):
        code = response_data["generated_code"]
        # Strip markdown fences if the LLM leaked them
        if code.startswith("```html"):
            code = code[7:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        response_data["generated_code"] = inject_auth_into_html(code.strip(), project_id)

    return response_data
