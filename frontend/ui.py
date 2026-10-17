import html
import inspect
import gradio as gr
from PIL import Image, ImageOps
import io
from backend.app.config import (get_settings)
from backend.app.models import DietProfile
from backend.app.services.analyzer import GeminiLabelAnalyzer

_analyzer = None

def analyze(image, profile):
    """Adapter: PIL image + profile dict -> dict, same contract as the stub."""
    global _analyzer
    if _analyzer is None:
        _analyzer = GeminiLabelAnalyzer(get_settings())
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=90)
    result = _analyzer.analyze(
        buf.getvalue(), "image/jpeg", DietProfile.model_validate(profile)
    )
    return result.model_dump(mode="json")

ALLERGENS = [
    "cereals containing gluten", "crustaceans", "eggs", "fish", "peanuts",
    "soybeans", "milk", "tree nuts", "celery", "mustard", "sesame",
    "sulphur dioxide and sulphites", "lupin", "molluscs",
]
DIETS = ["vegetarian", "vegan", "halal", "kosher", "pescatarian"]
GOALS = ["less sugar", "less salt"]
DEFAULT_PROFILE = {"diets": [], "allergens": [], "goals": []}

NOTICE = ("Check the physical package if you have an allergy. "
          "Label Lens is an aid, not medical advice.")

CSS = """
:root, .gradio-container {
  --ll-bg: #fff8ec; --ll-card: #ffffff; --ll-ink: #1d2b24;
  --ll-green: #17a05d; --ll-green-dark: #0f7a45; --ll-orange: #ff8a3d;
  --ll-sun: #ffd166; --ll-line: #f0e2c8;
}
body, .gradio-container {
  background: linear-gradient(180deg, #fff3d6 0%, #fff8ec 220px) !important;
  color: var(--ll-ink) !important;
}
.gradio-container { max-width: 560px !important; margin: 0 auto !important; padding: 12px !important; font-size: 18px !important; }
.gradio-container h1 { font-size: 2.2rem !important; margin: 4px 0 0 !important; color: var(--ll-green-dark) !important; }
.gradio-container p, .gradio-container label, .gradio-container span { font-size: 1.05rem; }

/* step banners */
.ll-step { display: flex; align-items: center; gap: 10px; margin: 14px 0 8px; font-weight: 700; font-size: 1.15rem; color: var(--ll-ink); }
.ll-step b { background: var(--ll-orange); color: #fff; width: 34px; height: 34px; border-radius: 50%;
             display: inline-flex; align-items: center; justify-content: center; font-size: 1.1rem; flex: none; }

/* profile at the top */
.ll-profile { border: 2px solid var(--ll-sun) !important; border-radius: 20px !important; background: #fffdf5 !important; }
.ll-profile > button, .ll-profile .label-wrap { min-height: 64px !important; font-size: 1.2rem !important; font-weight: 700 !important; }
.ll-profile fieldset { border: 0 !important; }
.ll-profile .wrap { gap: 10px !important; }
.ll-profile label {
  min-height: 52px !important; padding: 10px 16px !important; border-radius: 999px !important;
  border: 2px solid var(--ll-line) !important; background: #fff !important; font-size: 1.05rem !important;
  display: inline-flex !important; align-items: center !important; cursor: pointer;
}
.ll-profile label.selected { background: var(--ll-green) !important; border-color: var(--ll-green-dark) !important; color: #fff !important; }
.ll-profile label.selected span { color: #fff !important; }
.ll-profile input[type=checkbox] { width: 24px; height: 24px; accent-color: var(--ll-orange); }
.ll-summary {
  background: #e8f8ef !important;
  border: 0 !important;
  border-left: 6px solid var(--ll-green) !important;
  border-radius: 14px !important;
  box-shadow: none !important;
  padding: 4px 14px !important;
}
.ll-summary > *, .ll-summary .prose {
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
}
/* big action button */
button.lg, #analyze-btn {
  min-height: 72px !important; font-size: 1.4rem !important; font-weight: 800 !important;
  border-radius: 20px !important; border: 0 !important; color: #fff !important;
  background: linear-gradient(135deg, var(--ll-green), #3cc77f) !important;
  box-shadow: 0 6px 0 var(--ll-green-dark) !important; margin: 8px 0 14px !important;
}
button.lg:active { transform: translateY(4px); box-shadow: 0 2px 0 var(--ll-green-dark) !important; }

/* image area: bigger touch targets */
#scan-image { border: 3px dashed var(--ll-orange) !important; border-radius: 20px !important; background: #fff !important; }
#scan-image button { min-height: 52px; min-width: 52px; }

/* result card */
.ll-card { font-family: system-ui, sans-serif; line-height: 1.5; font-size: 1.1rem; }
.ll-verdict { border-radius: 22px; padding: 24px; color: #fff; margin-bottom: 16px; box-shadow: 0 6px 18px rgba(0,0,0,.15); }
.ll-verdict h2 { margin: 0 0 4px; font-size: 3.2rem; letter-spacing: .05em; color: #fff; }
.ll-verdict p { margin: 6px 0; color: #fff; font-size: 1.15rem; }
.ll-OK { background: linear-gradient(135deg, #17a05d, #3cc77f); }
.ll-CHECK { background: linear-gradient(135deg, #e08a00, #ffb02e); }
.ll-AVOID { background: linear-gradient(135deg, #d6342a, #ff6b5e); }
.ll-sec { margin: 16px 0; padding: 16px; background: var(--ll-card); border: 2px solid var(--ll-line); border-radius: 18px; }
.ll-sec h3 { margin: 0 0 10px; font-size: 1.25rem; color: var(--ll-green-dark); }
.ll-chip { display: inline-block; padding: 9px 16px; margin: 4px 6px 4px 0; border-radius: 999px;
           background: #fff0d6; border: 1px solid var(--ll-sun); font-size: 1.05rem; }
.ll-notice { border-left: 6px solid #d6342a; background: #fff1ef; }
.ll-retake { border: 3px dashed var(--ll-orange); background: #fff4e6; padding: 16px; border-radius: 16px; margin-bottom: 14px; font-size: 1.1rem; }
.ll-staff { background: #eaf6ff; border-color: #b9dcf5; }
.ll-staff-it { font-size: 1.5rem; }
.ll-sec ul { padding-left: 22px; } .ll-sec li { margin: 8px 0; font-size: 1.1rem; }
:root, .dark, .gradio-container, .gradio-container.dark {
  color-scheme: light;
  --body-text-color: #1d2b24 !important;
  --body-text-color-subdued: #4a5a52 !important;
  --block-label-text-color: #1d2b24 !important;
  --block-title-text-color: #1d2b24 !important;
  --block-info-text-color: #4a5a52 !important;
  --input-placeholder-color: #5b6b63 !important;
  --block-background-fill: #ffffff !important;
  --input-background-fill: #ffffff !important;
  --background-fill-primary: #ffffff !important;
  --background-fill-secondary: #fff8ec !important;
  --border-color-primary: #f0e2c8 !important;
}

/* upload area text ("Drop Image Here - or - Click to Upload") and icons */
#scan-image, #scan-image * { color: #33443b; }
#scan-image svg { color: #33443b; stroke: #33443b; }
#scan-image .or, #scan-image .wrap { font-size: 1.1rem; font-weight: 600; }

/* generic placeholders and small helper text */
input::placeholder, textarea::placeholder { color: #5b6b63 !important; opacity: 1 !important; }
.gradio-container .info, .gradio-container small { color: #4a5a52 !important; }

/* keep selected pills white-on-green */
.ll-profile label.selected, .ll-profile label.selected * { color: #fff !important; }
"""

FORCE_LIGHT_JS = """() => {
  const off = () => document.body.classList.remove('dark');
  off();
  new MutationObserver(off).observe(document.body, {attributes: true, attributeFilter: ['class']});
}"""

def esc(x):
    return html.escape(str(x))


def chips(items):
    return "".join(f'<span class="ll-chip">{esc(i)}</span>' for i in items) or "<em>none</em>"


def render(r: dict) -> str:
    retake = ""
    if not r.get("readable", True) or r.get("confidence") == "low":
        retake = ('<div class="ll-retake"><b>The label is hard to read.</b> '
                  "Retake the photo closer, flat, and without glare.</div>")
    v = r.get("verdict", "CHECK")
    if v not in ("OK", "CHECK", "AVOID"):
        v = "CHECK"
    reasons = "".join(f"<p>{esc(x)}</p>" for x in r.get("reasons", []))
    vocab = "".join(f"<li><b>{esc(w['it'])}</b> = {esc(w['en'])}</li>" for w in r.get("vocab", []))
    sp = r.get("staff_phrase", {})
    return f"""<div class="ll-card">
{retake}
<div class="ll-verdict ll-{v}"><h2>{v}</h2><p>{esc(r.get('product_name') or 'Unknown product')}</p>{reasons}</div>
<div class="ll-sec"><h3>Allergens detected</h3>{chips(r.get('allergens_detected', []))}
<p><small>Allergens not listed here were not detected on this label.</small></p></div>
<div class="ll-sec ll-notice">{NOTICE}</div>
<div class="ll-sec"><h3>Ingredients (English)</h3>{chips(r.get('ingredients_en', []))}</div>
<div class="ll-sec"><h3>Learn the words</h3><ul>{vocab}</ul></div>
<div class="ll-sec ll-staff"><h3>Ask the staff</h3><p><span class="ll-staff-it"><b>{esc(sp.get('it',''))}</b></span><br>{esc(sp.get('en',''))}</p></div>
</div>"""


def run(image, profile):
    if image is None:
        raise gr.Error("Take or upload a photo of the label first.")
    try:
        # fix phone orientation, drop alpha, cap size for speed (keeps text readable)
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        return render(analyze(image, profile or DEFAULT_PROFILE))
    except Exception as e:
        raise gr.Error(f"Analysis failed: {e}")


def load_profile(profile):
    p = profile or DEFAULT_PROFILE
    return p["diets"], p["allergens"], p["goals"]


def save_profile(diets, allergens, goals):
    return {"diets": diets, "allergens": allergens, "goals": goals}


def profile_summary(diets, allergens, goals):
    n = len(diets) + len(allergens) + len(goals)
    if n == 0:
        return "No profile set: results will be generic."
    parts = list(diets) + [f"no {a}" for a in allergens] + list(goals)
    return "Active profile: " + ", ".join(parts)


# --- Compatibility: Gradio versions differ in where css and webcam options go ---
IMG_PARAMS = inspect.signature(gr.Image.__init__).parameters
CAM = {"video": {
    "facingMode": {"ideal": "environment"},  # rear camera
    "width": {"ideal": 1920},
    "height": {"ideal": 1080},
}}
img_kwargs = {}
if "webcam_options" in IMG_PARAMS:
    img_kwargs["webcam_options"] = gr.WebcamOptions(mirror=False, constraints=CAM)
else:
    img_kwargs["mirror_webcam"] = False
    if "webcam_constraints" in IMG_PARAMS:
        img_kwargs["webcam_constraints"] = CAM

BLOCKS_PARAMS = inspect.signature(gr.Blocks.__init__).parameters
blocks_kwargs = {"title": "Label Lens"}
if "css" in BLOCKS_PARAMS:
    blocks_kwargs["css"] = CSS
if "js" in BLOCKS_PARAMS:
    blocks_kwargs["js"] = FORCE_LIGHT_JS  # always light theme, even if phone is in dark mode
if "theme" in BLOCKS_PARAMS:
    blocks_kwargs["theme"] = gr.themes.Soft(primary_hue="green", secondary_hue="orange")

with gr.Blocks(**blocks_kwargs) as demo:
    profile = gr.BrowserState(DEFAULT_PROFILE, storage_key="label_lens_profile")
    gr.Markdown("# Label Lens\nPhoto of an Italian label in, plain-English verdict out.")

    # 1. PROFILE (top)
    gr.HTML('<div class="ll-step"><b>1</b> Your food profile</div>')
    summary = gr.Markdown(profile_summary([], [], []), elem_classes="ll-summary")
    with gr.Accordion("Tap to set diet, allergies, goals", open=False, elem_classes="ll-profile"):
        diets = gr.CheckboxGroup(DIETS, label="Diet")
        allergens = gr.CheckboxGroup(ALLERGENS, label="Allergens to avoid")
        goals = gr.CheckboxGroup(GOALS, label="Goals")

    # 2. PHOTO
    gr.HTML('<div class="ll-step"><b>2</b> Photograph the ingredients (flat, well lit)</div>')
    img = gr.Image(sources=["upload", "webcam"], type="pil", label="Label photo",
                   height=340, elem_id="scan-image", **img_kwargs)

    # 3. ANALYZE
    gr.HTML('<div class="ll-step"><b>3</b> Get your verdict</div>')
    go = gr.Button("Analyze label", variant="primary", elem_classes="lg", elem_id="analyze-btn")
    out = gr.HTML()

    for c in (diets, allergens, goals):
        c.change(save_profile, [diets, allergens, goals], profile)
        c.change(profile_summary, [diets, allergens, goals], summary)
    demo.load(load_profile, profile, [diets, allergens, goals])
    go.click(run, [img, profile], out, scroll_to_output=True, show_progress="minimal")

if __name__ == "__main__":
    launch_kwargs = {"server_name": "0.0.0.0", "share": True}
    if "css" in inspect.signature(demo.launch).parameters:
        launch_kwargs["css"] = CSS
    demo.launch(**launch_kwargs)