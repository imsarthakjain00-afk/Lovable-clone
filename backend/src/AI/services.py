from google import genai as gemini_client
from src.utils.settings import settings


# Configure the Gemini client with the API key from environment settings.
# If no key is set, we fall back to a realistic simulation mode.
if settings.GEMINI_API_KEY:
    gemini_client_instance = gemini_client.Client(api_key=settings.GEMINI_API_KEY)
    GEMINI_MODEL_NAME = "gemini-2.0-flash"
    is_gemini_available = True
else:
    gemini_client_instance = None
    GEMINI_MODEL_NAME = None
    is_gemini_available = False


WEBSITE_CODE_GENERATION_PROMPT = """
You are an expert web developer AI assistant. A user wants you to build a website.
Your job is to generate complete, working HTML code (with embedded CSS and JavaScript) for the website.

IMPORTANT RULES:
1. Return ONLY the full HTML code. No explanations, no markdown code blocks.
2. Start with <!DOCTYPE html> and end with </html>.
3. Use modern design: dark background, clean typography, gradients, and subtle animations.
4. Make it fully responsive and mobile-friendly.
5. Use Google Fonts via a <link> tag.
6. Include inline CSS in a <style> tag and inline JS in a <script> tag.
7. Make it look premium and complete, not like a template placeholder.

User's request: {user_prompt}
"""


def build_gemini_prompt(user_prompt: str) -> str:
    """Format the user's prompt into the full AI instruction prompt."""
    return WEBSITE_CODE_GENERATION_PROMPT.format(user_prompt=user_prompt)


def generate_website_code_with_gemini(user_prompt: str) -> dict:
    """
    Send the user's prompt to Gemini and get back a complete website in HTML.
    Returns a dict with 'response_text' and 'generated_code'.
    """
    full_prompt = build_gemini_prompt(user_prompt)
    gemini_response = gemini_client_instance.models.generate_content(
        model=GEMINI_MODEL_NAME,
        contents=full_prompt
    )
    raw_output = gemini_response.text.strip()

    # Clean up in case Gemini wraps the code in markdown code fences
    if raw_output.startswith("```html"):
        raw_output = raw_output[7:]
    if raw_output.startswith("```"):
        raw_output = raw_output[3:]
    if raw_output.endswith("```"):
        raw_output = raw_output[:-3]

    generated_html_code = raw_output.strip()

    return {
        "response_text": "Your website has been generated successfully! Preview it in the panel on the right.",
        "generated_code": generated_html_code
    }


def generate_website_code_simulation(user_prompt: str) -> dict:
    """
    Fallback simulation when no Gemini API key is configured.
    Returns a fully functional demo website so the UI still works.
    """
    website_title = user_prompt[:50] if len(user_prompt) > 50 else user_prompt
    demo_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{website_title}</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', sans-serif;
      background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
      color: #ffffff;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    nav {{
      width: 100%;
      padding: 1.5rem 3rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(255,255,255,0.05);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }}
    .logo {{ font-size: 1.4rem; font-weight: 800; letter-spacing: -0.5px; }}
    .nav-links {{ display: flex; gap: 2rem; font-size: 0.9rem; opacity: 0.8; }}
    .hero {{
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 4rem 2rem;
      max-width: 800px;
    }}
    .hero-badge {{
      background: rgba(139, 92, 246, 0.2);
      border: 1px solid rgba(139, 92, 246, 0.4);
      color: #c4b5fd;
      padding: 0.4rem 1rem;
      border-radius: 999px;
      font-size: 0.8rem;
      margin-bottom: 1.5rem;
    }}
    h1 {{
      font-size: clamp(2.5rem, 6vw, 4.5rem);
      font-weight: 800;
      line-height: 1.1;
      margin-bottom: 1.5rem;
      background: linear-gradient(135deg, #fff 0%, #a78bfa 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .subtitle {{ font-size: 1.2rem; opacity: 0.7; margin-bottom: 2.5rem; line-height: 1.6; }}
    .cta-buttons {{ display: flex; gap: 1rem; flex-wrap: wrap; justify-content: center; }}
    .btn-primary {{
      background: linear-gradient(135deg, #7c3aed, #4f46e5);
      color: white;
      border: none;
      padding: 1rem 2rem;
      border-radius: 12px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 10px 30px rgba(124,58,237,0.4); }}
    .btn-secondary {{
      background: rgba(255,255,255,0.08);
      color: white;
      border: 1px solid rgba(255,255,255,0.2);
      padding: 1rem 2rem;
      border-radius: 12px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
    }}
    .features {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1.5rem;
      width: 100%;
      max-width: 900px;
      padding: 0 2rem 4rem;
    }}
    .feature-card {{
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 16px;
      padding: 2rem;
      text-align: center;
      transition: transform 0.2s;
    }}
    .feature-card:hover {{ transform: translateY(-4px); }}
    .feature-icon {{ font-size: 2rem; margin-bottom: 1rem; }}
    .feature-title {{ font-weight: 600; margin-bottom: 0.5rem; }}
    .feature-desc {{ font-size: 0.9rem; opacity: 0.6; }}
  </style>
</head>
<body>
  <nav>
    <div class="logo">✦ {website_title[:20]}</div>
    <div class="nav-links">
      <span>Features</span>
      <span>Pricing</span>
      <span>About</span>
    </div>
  </nav>
  <section class="hero">
    <div class="hero-badge">✨ AI Generated Website</div>
    <h1>{website_title}</h1>
    <p class="subtitle">A beautiful, responsive website built with AI in seconds. Customize it to match your brand and vision.</p>
    <div class="cta-buttons">
      <button class="btn-primary">Get Started Free</button>
      <button class="btn-secondary">Learn More</button>
    </div>
  </section>
  <section class="features">
    <div class="feature-card">
      <div class="feature-icon">🚀</div>
      <div class="feature-title">Lightning Fast</div>
      <div class="feature-desc">Optimized for performance and speed out of the box.</div>
    </div>
    <div class="feature-card">
      <div class="feature-icon">🎨</div>
      <div class="feature-title">Beautiful Design</div>
      <div class="feature-desc">Modern, clean UI with premium aesthetics.</div>
    </div>
    <div class="feature-card">
      <div class="feature-icon">📱</div>
      <div class="feature-title">Fully Responsive</div>
      <div class="feature-desc">Works perfectly on all screen sizes and devices.</div>
    </div>
  </section>
</body>
</html>"""

    return {
        "response_text": (
            f"Here is your generated website for: \"{user_prompt}\". "
            "Preview it in the panel on the right. (Note: Running in simulation mode — add GEMINI_API_KEY to .env for real AI generation.)"
        ),
        "generated_code": demo_html
    }


def generate_website_code(user_prompt: str) -> dict:
    """
    Main entry point for code generation.
    Uses Gemini if the API key is configured, otherwise uses the simulation.
    """
    if is_gemini_available:
        return generate_website_code_with_gemini(user_prompt)
    else:
        return generate_website_code_simulation(user_prompt)
