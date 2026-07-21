"""
Generation Pipeline
===================
Streams the full HTML website using the active LLM provider.
Provider is selected via LLM_PROVIDER env variable (gemini | groq).
"""
import logging
import json

from src.AI.memory.brain import ProjectBrain, DesignBrain
from src.AI.memory.tokens import DesignTokens
from src.events.bus import EventBus
from src.utils.llm_retry import with_retry, RetryPolicy
from src.AI.llm.provider import get_llm_provider

logger = logging.getLogger(__name__)


WEBSITE_SYSTEM_PROMPT = """You are a world-class senior frontend engineer at a top design agency. Your job is to build stunning, production-grade websites that would impress a Fortune 500 client.

OUTPUT FORMAT — NON-NEGOTIABLE:
- Output ONLY raw HTML. Start with <!DOCTYPE html>, end with </html>.
- NO markdown fences, NO explanations, NO comments outside the HTML.

═══════════════════════════════════════
 ABSOLUTE PROHIBITIONS (NEVER DO THESE)
═══════════════════════════════════════
✗ NEVER use "Lorem ipsum" — write real, specific, compelling copy for the actual business
✗ NEVER use broken <img> tags — every image MUST use a real working URL (see IMAGE RULES)
✗ NEVER put light/white text on a light/yellow/white background — this makes text INVISIBLE
✗ NEVER use generic names like "Product 1", "John Doe", "Our Service" — invent real names
✗ NEVER leave placeholder text like "Your tagline here" or "Description goes here"
✗ NEVER use a plain white (#fff) background for the hero section
✗ NEVER add Firebase or Supabase <script> tags — they are already injected
✗ NEVER generate a single-page site when multi-page is requested — ALL pages must exist

═══════════════════════════════════════
 IMAGE RULES — ALWAYS FOLLOW
═══════════════════════════════════════
Every <img> MUST use a real, high-resolution working URL:

  FORMAT: https://picsum.photos/seed/{DESCRIPTIVE_KEYWORD}/{WIDTH}/{HEIGHT}

Examples by use case:
  • Hero banner (local shop):   https://picsum.photos/seed/shop-hero-front/1200/600
  • Product card (food):        https://picsum.photos/seed/fresh-organic-apples/400/400
  • Team avatar:                https://picsum.photos/seed/store-owner-portrait/100/100
  • Services (medical):         https://picsum.photos/seed/hospital-doctor-care/600/400
  • Background (restaurant):    https://picsum.photos/seed/restaurant-dining-room/1920/1080

RULES:
1. Use descriptive seed words in the URL matching the business content (e.g. `bakery-bread`, `grocery-shelf`, `team-priya`).
2. Use DIFFERENT seed words for EVERY image so each photo is unique.
3. ALWAYS add: loading="lazy" alt="[descriptive text]" style="width:100%;object-fit:cover"

═══════════════════════════════════════
 DESIGN STANDARDS — MANDATORY
═══════════════════════════════════════
1. COLOR CONTRAST: Every text element MUST have sufficient contrast with its background.
   - Dark backgrounds (#0a0a0a to #1e1e2e) → use white/light text (#f0f0f0, #e2e8f0)
   - Light backgrounds (#f8f8f8 to #ffffff) → use dark text (#111827, #1f2937)
   - NEVER put white text on white/yellow/light backgrounds
   - NEVER put dark text on dark backgrounds

2. HERO SECTION: Must be visually spectacular — this is the first impression.
   - Use a dark gradient, rich color, or full-bleed image background
   - Large, bold headline (4xl+) with clear contrast
   - Subtitle text must be readable against the hero background
   - Include a prominent CTA button with hover effects

3. TYPOGRAPHY: 
   - Import a Google Font (Inter, Sora, Plus Jakarta Sans, or similar)
   - Use font-weight hierarchy: 700+ for headings, 400-500 for body
   - Line height 1.6+ for body text

4. COLOR PALETTE: Use a cohesive palette — pick ONE of these approaches:
   - Dark premium: Background #0a0a0f, Cards #13131a, Accent #6366f1 or #8b5cf6
   - Dark warm: Background #0d0d0d, Cards #1a1a1a, Accent #f59e0b or #ef4444
   - Light minimal: Background #f9fafb, Cards #ffffff, Accent #3b82f6 or #10b981
   NEVER mix random colors — be deliberate and consistent.

5. CARDS & SECTIONS: Each card/item must have:
   - Proper padding (p-6 or p-8)
   - Rounded corners (rounded-xl or rounded-2xl)
   - Subtle border or shadow
   - Hover state (scale or shadow increase)

6. CONTENT: Write like a copywriter, not a developer:
   - Invent a real brand name, real product names, real prices
   - Write 1-2 sentence compelling descriptions for each product/service
   - Use real-sounding testimonial names (Priya Sharma, James O'Brien, etc.)
   - Stats must be specific: "12,000+ customers" not "many customers"

═══════════════════════════════════════
 REQUIRED SECTIONS
═══════════════════════════════════════
Every website must include ALL of these:
1. Navigation bar — sticky, with logo, links, and CTA button
2. Hero section — full-viewport, visually stunning, with headline + subtitle + CTA
3. Features/Products/Services section — grid of cards with images, titles, descriptions
4. Social proof — testimonials with real names and avatars OR stats with specific numbers
5. CTA section — prominent call-to-action with contrasting background
6. Footer — with logo, links, social icons (inline SVG), copyright

═══════════════════════════════════════
 AUTHENTICATION (PRE-INJECTED)
═══════════════════════════════════════
The platform auto-injects Firebase Auth + Supabase. Available at runtime:
  window.signInWithGoogle() / window.signInWithEmail(email, password)
  window.signUpWithEmail(email, password, name) / window.signOutUser()
  window.supabaseDb  — for storing app data
When auth is needed: build a clean modal with Login/Signup tabs. Wire to these helpers.
DO NOT add firebase/supabase <script> tags — already injected.

═══════════════════════════════════════
 ANIMATIONS
═══════════════════════════════════════
Add these CSS animations at minimum:
- @keyframes fadeInUp { from { opacity:0; transform:translateY(20px) } to { opacity:1; transform:translateY(0) } }
- Hover transitions on all cards and buttons (0.2s ease)
- Sticky nav with box-shadow on scroll (via JS scroll listener)"""


def _build_image_context(images: list) -> str:
    """Build the image section of the prompt using clean placeholder tokens."""
    if not images:
        return ""
    lines = [
        "\n═══════════════════════════════════════",
        " USER UPLOADED IMAGES (CRITICAL MANDATE)",
        "═══════════════════════════════════════",
        "The user uploaded custom images for this website. You MUST embed them in key sections (e.g. hero image, logo, feature cards, or product showcase).",
        "Use these EXACT string tokens as the src attribute values in your <img> tags:"
    ]
    for i, img in enumerate(images):
        name = img.get("name", f"Image_{i+1}")
        token = f"UPLOADED_IMAGE_{i+1}"
        lines.append(f"  • Image {i+1} ({name}) → Use src=\"{token}\" (e.g. <img src=\"{token}\" alt=\"{name}\" class=\"...\">)")
    lines.append("\nRULES FOR UPLOADED IMAGES:")
    lines.append("1. Do NOT write raw base64 data. Use the exact tokens `UPLOADED_IMAGE_1`, `UPLOADED_IMAGE_2`, etc. as the src string.")
    lines.append("2. Make uploaded images prominent — place UPLOADED_IMAGE_1 in the Hero section or Navbar logo, and others in feature/product cards.")
    lines.append("3. Always add styling (e.g. rounded corners, object-fit: cover, max-height, drop-shadow).")
    return "\n".join(lines)


def _replace_image_placeholders(html_code: str, images: list) -> str:
    """Post-process HTML: replace placeholder tokens with actual base64 data URIs."""
    if not images or not html_code:
        return html_code
    
    clean_html = html_code
    for i, img in enumerate(images):
        data_url = img.get("dataUrl") or img.get("data_url", "")
        if not data_url or not data_url.startswith("data:image"):
            continue
        
        token = f"UPLOADED_IMAGE_{i+1}"
        alt_token_1 = f"FULL_DATA_URI_{i+1}"
        alt_token_2 = f"FULL_DATA_URI_{i}"
        
        # Replace tokens across all possible variations
        clean_html = clean_html.replace(token, data_url)
        clean_html = clean_html.replace(alt_token_1, data_url)
        clean_html = clean_html.replace(alt_token_2, data_url)
        
    return clean_html


def _build_generation_prompt(brain: ProjectBrain, design_brain: DesignBrain, design_tokens: DesignTokens, is_edit: bool = False, edit_prompt: str = None, current_code: str = None, images: list = None, arch_context: str = "") -> str:
    """Compose the full generation prompt with all available context."""

    # ── 1. Extract project facts ──────────────────────────────────────────────
    facts = []
    page_type = "single-page"
    arch_pages = []
    arch_nav = []

    for fact in (brain.memory.project_facts or []):
        if fact.startswith("deployed_url:"):
            continue
        if fact.startswith("page_type:"):
            page_type = fact.replace("page_type:", "").strip()
            continue
        if fact.startswith("architecture:"):
            try:
                import re as _re
                arch_data = json.loads(fact.replace("architecture:", "", 1))
                arch_pages = arch_data.get("pages", [])
                arch_nav   = arch_data.get("nav_items", arch_data.get("sections", []))
            except Exception:
                pass
            continue
        clean = fact.replace("user_idea: ", "").replace("user_idea:", "").strip()
        if clean:
            facts.append(f"- {clean}")

    # Fallback: decisions dict
    if not facts and brain.memory and brain.memory.decisions:
        for key, decision in brain.memory.decisions.items():
            if key == "page_structure":
                page_type = decision.value or page_type
                continue
            if decision.status in ("confirmed", "inferred") and decision.value:
                facts.append(f"- {key.replace('_', ' ').title()}: {decision.value}")

    facts_str = "\n".join(facts) if facts else "- General purpose website"
    is_multi = "multi" in page_type.lower()

    # ── 2. Design style warning ───────────────────────────────────────────────
    design_id   = brain.design_id or ""
    design_name = design_id.replace("external_", "").replace("_", " ").title() if design_id else "Custom"
    design_style_warning = f"""
CRITICAL — DESIGN VS CONTENT SEPARATION:
  The user selected the "{design_name}" design template.
  USE ITS VISUAL STYLE (colors, typography, spacing, card shapes, layout) ONLY.
  DO NOT copy any content, brand name, taglines, or business type from that template.
  The website is FOR THE USER'S BUSINESS described in "Project Requirements" below.
  Every headline, product name, and text MUST be about the user's actual business.
  NEVER mention "{design_name}", Airbnb, or any unrelated brand in the output.
"""

    # ── 3. Blueprint summary ──────────────────────────────────────────────────
    blueprint_str = ""
    if brain.blueprint:
        try:
            bp = brain.blueprint.model_dump()
            blueprint_str = f"""
Website Blueprint:
- Pages: {', '.join(bp.get('pages', ['Home']))}
- Navigation: {', '.join(bp.get('navigation', []))}
- Key sections: {json.dumps(bp.get('sections', {}), indent=2)}
- Forms needed: {', '.join(bp.get('forms', []))}
- Cards/listings: {', '.join(bp.get('cards', []))}
"""
        except Exception:
            blueprint_str = ""

    # ── 4. Design spec ────────────────────────────────────────────────────────
    design_str = ""
    if design_brain:
        try:
            d = design_brain.model_dump()
            design_str = f"""
Visual Design Specification (apply to user's content only):
- Typography: {json.dumps(d.get('typography', {}), indent=2)}
- Color tokens: {json.dumps(d.get('color_tokens', {}), indent=2)}
- Border radius: {d.get('border_radius', 'rounded')}
- Spacing: {d.get('spacing', '8px base')}
- Grid: {d.get('grid_system', '12-column')}
- Desktop: {d.get('desktop_strategy', '')}
- Mobile: {d.get('mobile_strategy', '')}
- Interactions: {d.get('interaction_philosophy', '')}
"""
        except Exception:
            design_str = ""

    # ── 5. Token spec ─────────────────────────────────────────────────────────
    tokens_str = ""
    if design_tokens:
        try:
            t = design_tokens.model_dump()
            tokens_str = f"""
Concrete Design Tokens (USE THESE EXACT VALUES for styling):
{json.dumps(t, indent=2)}
"""
        except Exception:
            tokens_str = ""

    images_context = _build_image_context(images or [])

    # ── 6. Edit mode ──────────────────────────────────────────────────────────
    if is_edit and current_code and edit_prompt:
        return f"""You are updating an existing website based on a user's request.

USER EDIT REQUEST: "{edit_prompt}"
{images_context}

Here is the CURRENT website code:
```html
{current_code}
```

CRITICAL OUTPUT RULES:
1. Output ONLY raw HTML starting with <!DOCTYPE html> and ending with </html>.
2. Embed all CSS in a <style> tag in <head>.
3. Include Tailwind CSS via CDN.
4. Apply the user's requested changes flawlessly. DO NOT remove existing functionality unless requested.
5. If the user provided images, embed them using the exact data URIs provided above.
6. Do not output anything other than the new HTML.

Generate the updated website now:"""

    # ── 7. New generation — multi-page or single-page ─────────────────────────
    is_multi = "multi" in page_type.lower()

    if is_multi:
        pages = arch_pages or ["Home", "About", "Products", "Contact"]
        page_ids = [p.lower().replace(" ", "-") for p in pages]
        first_page = page_ids[0] if page_ids else "home"

        return f"""Generate a complete multi-page website as a SINGLE HTML FILE using JavaScript hash routing.

{design_style_warning}

Project Requirements (THIS IS WHAT THE WEBSITE IS ABOUT):
{facts_str}
{blueprint_str}
{design_str}
{tokens_str}
{arch_context}
{images_context}

CRITICAL IMAGE REQUIREMENT FOR THIS SITE:
Choose descriptive seed keywords for picsum.photos matching this specific business.
Format: https://picsum.photos/seed/[descriptive-word]/[WIDTH]/[HEIGHT]
Example for a local shop: https://picsum.photos/seed/grocery-store-hero/1200/600 or https://picsum.photos/seed/fresh-fruits/400/400
Example for a restaurant: https://picsum.photos/seed/gourmet-dishes/400/400

MULTI-PAGE ARCHITECTURE — MANDATORY IMPLEMENTATION PATTERN:

⚠️  YOU MUST OUTPUT ALL {len(pages)} PAGES IN THIS SINGLE HTML FILE.

The pages are: {', '.join(pages)} (IDs: {', '.join(page_ids)})

COPY THIS STRUCTURE EXACTLY:

<body>
  <!-- Navigation bar present on ALL pages -->
  <nav class="navbar border-b border-gray-800 bg-gray-900/90 backdrop-blur sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 flex justify-between items-center h-16">
      <a href="#home" class="font-bold text-xl text-white">Brand Logo</a>
      <div class="flex space-x-6">
        <a href="#home" data-page="home" class="nav-link text-gray-300 hover:text-white px-3 py-2 text-sm font-medium" onclick="showPage('home'); return false;">Home</a>
        <a href="#about" data-page="about" class="nav-link text-gray-300 hover:text-white px-3 py-2 text-sm font-medium" onclick="showPage('about'); return false;">About Us</a>
        <a href="#products" data-page="products" class="nav-link text-gray-300 hover:text-white px-3 py-2 text-sm font-medium" onclick="showPage('products'); return false;">Products</a>
        <a href="#contact" data-page="contact" class="nav-link text-gray-300 hover:text-white px-3 py-2 text-sm font-medium" onclick="showPage('contact'); return false;">Contact</a>
      </div>
    </div>
  </nav>

  <!-- PAGE 1 (HOME) - MUST HAVE style="display: block;" DIRECTLY IN HTML -->
  <section class="page-section" id="page-{page_ids[0]}" style="display: block;">
    <!-- FULL Home page content here — hero, features grid, product preview, testimonials, CTA -->
  </section>

  <!-- PAGE 2 (ABOUT) - style="display: none;" -->
  <section class="page-section" id="page-{page_ids[1] if len(page_ids) > 1 else 'about'}" style="display: none;">
    <!-- FULL About page content here — team, mission, company history, values -->
  </section>

  <!-- PAGE 3 (PRODUCTS / SERVICES) - style="display: none;" -->
  <section class="page-section" id="page-{page_ids[2] if len(page_ids) > 2 else 'products'}" style="display: none;">
    <!-- FULL Products page content here — product cards grid with picsum images, pricing, specs -->
  </section>

  <!-- PAGE 4 (CONTACT) - style="display: none;" -->
  <section class="page-section" id="page-{page_ids[3] if len(page_ids) > 3 else 'contact'}" style="display: none;">
    <!-- FULL Contact page content here — contact form with Name, Email, Message, Submit button, map & address -->
  </section>

  <!-- Footer on ALL pages -->
  <footer class="bg-gray-900 border-t border-gray-800 text-gray-400 py-12">
    ...
  </footer>

  <!-- FOOLPROOF JS ROUTER (RUNS IMMEDIATELY, NO DOMCONTENTLOADED WRAPPER) -->
  <script>
    function showPage(targetId) {{
      if (!targetId) targetId = '{first_page}';
      targetId = targetId.replace('#', '').replace('page-', '');

      var sections = document.querySelectorAll('.page-section');
      sections.forEach(function(sec) {{
        var sId = sec.id.replace('page-', '');
        sec.style.display = (sId === targetId) ? 'block' : 'none';
      }});

      var navLinks = document.querySelectorAll('.nav-link');
      navLinks.forEach(function(link) {{
        var linkTarget = (link.getAttribute('data-page') || link.getAttribute('href') || '').replace('#', '').replace('page-', '');
        if (linkTarget === targetId) {{
          link.classList.add('text-indigo-400', 'font-bold');
        }} else {{
          link.classList.remove('text-indigo-400', 'font-bold');
        }}
      }});
    }}

    // Execute immediately on script parse so initial page renders instantly inside preview iframes
    (function() {{
      var curHash = (window.location.hash || '').replace('#', '').replace('page-', '');
      showPage(curHash || '{first_page}');
    }})();

    window.addEventListener('hashchange', function() {{
      var curHash = (window.location.hash || '').replace('#', '').replace('page-', '');
      showPage(curHash || '{first_page}');
    }});
  </script>
</body>

PER-PAGE CONTENT MANDATE:
- Do NOT generate thin or empty pages.
- Every single page section MUST contain at least 3 distinct content blocks (e.g. Hero/Banner + Cards/Grid + Details/Form).
- Output ONLY raw HTML from <!DOCTYPE html> to </html>.

Build the complete multi-page website now — ALL {len(pages)} pages:"""

    # Single-page
    return f"""Generate a complete, stunning, single-page HTML website with all sections on one scrollable page.

{design_style_warning}

Project Requirements (THIS IS WHAT THE WEBSITE IS ABOUT):
{facts_str}
{blueprint_str}
{design_str}
{tokens_str}
{arch_context}
{images_context}

CRITICAL IMAGE REQUIREMENT FOR THIS SITE:
Use picsum.photos seed URLs that MATCH this specific business.
For every <img> use: https://picsum.photos/seed/[descriptive-word]/[WIDTH]/[HEIGHT]
Example for a local shop: https://picsum.photos/seed/grocery-store-hero/1200/600 or https://picsum.photos/seed/fresh-fruits/400/400
Example for a restaurant: https://picsum.photos/seed/gourmet-dishes/400/400
Use DIFFERENT descriptive seed words for every image so they look distinct.

CRITICAL OUTPUT RULES:
1. Output ONLY raw HTML starting with <!DOCTYPE html> ending with </html>
2. Embed all CSS in a <style> tag in <head>
3. Include Tailwind CSS: <script src="https://cdn.tailwindcss.com"></script>
4. Include Google Fonts matching the design spec
5. ALL text must be specifically about the user's actual business — never generic
6. Nav links use smooth scroll to anchor sections on the same page
7. Hero section must be visually spectacular with content specific to this business
8. Every section must have proper padding, visual hierarchy, and contrast
9. Footer with links, copyright, and social icons (inline SVGs)
10. Mobile hamburger menu if more than 3 nav items
11. CONTACT FORM REQUIREMENT: If there is a 'Contact' section, you MUST build a full contact form (fields for Name, Email, Phone, Message, and a Submit button). Do not just list addresses.

Build the website now:"""


@with_retry(RetryPolicy(max_retries=1))
async def execute_generation_pipeline(brain: ProjectBrain, design_brain: DesignBrain, design_tokens: DesignTokens, **kwargs):
    """
    Multi-stage generation pipeline:
    Stage 1 - Component Architecture: LLM defines the page structure as a blueprint JSON.
    Stage 2 - Code Generation: LLM uses the architecture to write perfect HTML.

    Publishes code_chunk events for real-time preview and generation_complete when done.
    """
    project_id = kwargs.get("project_id")
    db = kwargs.get("db")
    user_prompt = kwargs.get("user_prompt")
    current_code = kwargs.get("current_code")
    images = kwargs.get("images", [])

    is_edit = bool(user_prompt and current_code)

    await EventBus.publish("generation_progress", {
        "project_id": project_id, "step": "Initializing Generation Engine", "status": "completed"
    })

    try:
        llm = get_llm_provider()
    except Exception as e:
        logger.error(f"Failed to initialize LLM provider: {e}")
        await EventBus.publish("generation_failed", {"project_id": project_id, "error": str(e)})
        return

    # Stage 1: Component Architecture Planning (only for new generations)
    architecture_blueprint = ""
    if not is_edit:
        await EventBus.publish("generation_progress", {
            "project_id": project_id, "step": "Planning Architecture", "status": "in_progress"
        })

        # ── Read project facts (same logic as _build_generation_prompt) ────────
        arch_facts = []
        for fact in (brain.memory.project_facts or []):
            if fact.startswith("architecture:") or fact.startswith("deployed_url:"):
                continue
            clean = fact.replace("user_idea: ", "").replace("user_idea:", "").strip()
            if clean:
                arch_facts.append(f"- {clean}")
        # Fallback to decisions
        if not arch_facts and brain.memory and brain.memory.decisions:
            for key, decision in brain.memory.decisions.items():
                if decision.status in ("confirmed", "inferred") and decision.value:
                    arch_facts.append(f"- {key.replace('_', ' ').title()}: {decision.value}")
        facts_str = "\n".join(arch_facts) if arch_facts else "- General purpose website"

        design_id = brain.design_id or ""
        design_name = design_id.replace("external_", "").replace("_", " ").title() if design_id else "Custom"

        arch_prompt = f"""You are a senior frontend architect planning a website structure.

The user has selected the "{design_name}" visual design style (colors/typography only).
The website content MUST be entirely about the user's actual business described below.
DO NOT generate content for {design_name} or any other brand — only for the user's business.

User's Business / Project Requirements:
{facts_str}

Design a component architecture plan in JSON format for THIS SPECIFIC BUSINESS. Include:
- page_sections: array of section names in order (e.g., ["navbar", "hero", "products", "testimonials", "cta", "footer"])
- navbar_items: array of nav link labels relevant to this business
- hero_headline: compelling main headline specifically for this business (not generic)
- hero_subtext: 1-sentence tagline specifically for this business
- color_scheme: {{primary, background, surface, text, accent}} hex values matching the {design_name} aesthetic
- font_family: name of Google Font to use
- unique_features: array of 2-3 standout sections specific to this type of business

Output ONLY valid JSON, nothing else."""

        try:
            arch_raw = await llm.complete(
                messages=[{"role": "user", "content": arch_prompt}],
                max_tokens=800, temperature=0.3
            )
            import re
            match = re.search(r'(\{.*\})', arch_raw, re.DOTALL)
            if match:
                architecture_blueprint = match.group(1)
                logger.info(f"[GENERATION] Stage 1 architecture: {architecture_blueprint[:200]}...")
        except Exception as e:
            logger.warning(f"[GENERATION] Stage 1 architecture failed (non-fatal): {e}")

        await EventBus.publish("generation_progress", {
            "project_id": project_id, "step": "Planning Architecture", "status": "completed"
        })

        # Remove the old duplicate block below

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 2: Full Code Generation
    # ─────────────────────────────────────────────────────────────────────────
    await EventBus.publish("generation_progress", {
        "project_id": project_id, "step": "Writing HTML & CSS", "status": "in_progress"
    })
    
    # Inject architecture blueprint into prompt if available
    arch_context = ""
    if architecture_blueprint:
        arch_context = f"\n\nARCHITECTURE PLAN (follow this precisely):\n{architecture_blueprint}\n"

    prompt = _build_generation_prompt(
        brain, design_brain, design_tokens, 
        is_edit=is_edit, edit_prompt=user_prompt, current_code=current_code,
        images=images,
        arch_context=arch_context,
    )
    
    messages = [
        {"role": "system", "content": WEBSITE_SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    
    full_html = ""
    try:
        async for chunk in llm.stream(messages, max_tokens=8000, temperature=0.7):
            full_html += chunk
            await EventBus.publish("code_chunk", {
                "project_id": project_id,
                "type": "code_chunk",
                "text": chunk
            })
                
    except Exception as e:
        logger.error(f"Generation streaming failed: {e}")
        await EventBus.publish("generation_failed", {
            "project_id": project_id,
            "type": "generation_failed",
            "error": str(e)
        })
        return
    
    # Strip any markdown fences that leaked through
    import re as _re
    clean_html = full_html.strip()
    if clean_html.startswith("```"):
        clean_html = _re.sub(r'^```(html)?\s*', '', clean_html, flags=_re.IGNORECASE)
        clean_html = _re.sub(r'\s*```\s*$', '', clean_html)
    
    # Replace uploaded image tokens with actual data URIs
    clean_html = _replace_image_placeholders(clean_html, images)
    
    await EventBus.publish("generation_progress", {
        "project_id": project_id, "step": "Writing HTML & CSS", "status": "completed"
    })

    # ── Step A: Split into virtual file manifest ─────────────────────────────
    await EventBus.publish("generation_progress", {
        "project_id": project_id, "step": "Building File Structure", "status": "in_progress"
    })

    from src.AI.pipelines.html_splitter import split_html_into_files
    file_manifest = split_html_into_files(clean_html, project_id=project_id or 0)

    await EventBus.publish("generation_progress", {
        "project_id": project_id, "step": "Building File Structure", "status": "completed"
    })

    # ── Step B: Auto-run Supabase migrations for this project ─────────────────
    await EventBus.publish("generation_progress", {
        "project_id": project_id, "step": "Provisioning Database", "status": "in_progress"
    })

    migration_ok = await _run_supabase_migrations(
        file_manifest.get("supabase/migrations/001_init.sql", ""),
        file_manifest.get("supabase/migrations/002_app.sql",  ""),
        project_id=project_id,
    )

    await EventBus.publish("generation_progress", {
        "project_id": project_id, "step": "Provisioning Database",
        "status": "completed" if migration_ok else "warning"
    })

    # ── Step C: Persist versioned manifest to Postgres ────────────────────────
    if db and project_id:
        try:
            from src.Projects import db_queries
            db_queries.save_project_version(
                project_id, file_manifest,
                commit_message="AI generation",
                db=db
            )
            logger.info(f"[GENERATION] Saved versioned manifest for project {project_id} ({len(file_manifest)} files)")
        except Exception as e:
            logger.error(f"Failed to save version to DB: {e}")

    # ── Step D: Broadcast completion to frontend ──────────────────────────────
    await EventBus.publish("generation_complete", {
        "project_id": project_id,
        "type": "generation_complete",
        "generated_code": clean_html,
        "file_manifest": {
            path: content for path, content in file_manifest.items()
            if path != "index.html"
        },
    })

    logger.info(f"[GENERATION] Complete for project {project_id} — {len(clean_html)} chars, {len(file_manifest)} files")



async def _run_supabase_migrations(sql_001: str, sql_002: str, project_id: int) -> bool:
    """
    Executes the two SQL migration files against Supabase using the service-role key.
    Each statement is scoped to project_id so projects are fully isolated.
    Returns True on success, False on failure (non-fatal — website still works).
    """
    import httpx
    from src.utils.settings import settings

    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY

    if not url or not key:
        logger.warning("[MIGRATION] Supabase credentials not configured — skipping migrations")
        return False

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    # Supabase exposes a SQL execution endpoint via the REST API on /rest/v1/rpc
    # but we need to use the pg endpoint directly. The safest cross-version approach
    # is to POST to /rest/v1/ with raw SQL via the postgres extension endpoint.
    # Use the Management API instead: POST /pg/query
    sql_endpoint = f"{url}/rest/v1/rpc/exec_sql"

    all_sql = f"-- Project {project_id} migrations\n\n{sql_001}\n\n{sql_002}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                sql_endpoint,
                json={"sql": all_sql},
                headers=headers,
            )
            if resp.status_code in (200, 201, 204):
                logger.info(f"[MIGRATION] Project {project_id} migrations OK")
                return True
            else:
                # Fallback: try Supabase's pg/query endpoint (newer versions)
                resp2 = await client.post(
                    f"{url}/pg/query",
                    json={"query": all_sql},
                    headers=headers,
                )
                if resp2.status_code in (200, 201, 204):
                    logger.info(f"[MIGRATION] Project {project_id} migrations OK (pg/query)")
                    return True

                logger.warning(
                    f"[MIGRATION] Migration API returned {resp.status_code}. "
                    f"SQL saved in file_manifest for manual execution."
                )
                return False
    except Exception as e:
        logger.warning(f"[MIGRATION] Non-fatal migration error: {e}")
        return False
