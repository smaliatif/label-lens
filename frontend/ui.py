import html
import inspect
import gradio as gr
from PIL import Image, ImageOps

# TODO: quando A pusha, cambiare in: from <file_di_A> import analyze
from analyze_stub import analyze

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
.gradio-container { max-width: 520px !important; margin: 0 auto !important; padding: 8px !important; }
.ll-card { font-family: system-ui, sans-serif; line-height: 1.45; }
.ll-verdict { border-radius: 16px; padding: 20px; color: #fff; margin-bottom: 14px; }
.ll-verdict h2 { margin: 0 0 4px; font-size: 2.4rem; letter-spacing: .04em; color: #fff; }
.ll-verdict p { margin: 4px 0; color: #fff; font-size: 1.05rem; }
.ll-OK { background: #1f7a4d; } .ll-CHECK { background: #a86a00; } .ll-AVOID { background: #b3261e; }
.ll-sec { margin: 16px 0; } .ll-sec h3 { margin: 0 0 6px; font-size: 1.05rem; }
.ll-chip { display: inline-block; padding: 6px 12px; margin: 3px 4px 3px 0;
           border-radius: 999px; background: rgba(128,128,128,.18); font-size: .95rem; }
.ll-notice { border-left: 4px solid #b3261e; padding: 10px 12px; background: rgba(179,38,30,.1); border-radius: 6px; }
.ll-retake { border: 2px dashed #a86a00; padding: 12px; border-radius: 10px; margin-bottom: 12px; }
.ll-staff-it { font-size: 1.25rem; }
.ll-hint { margin: 0 0 6px; opacity: .75; font-size: .95rem; }

/* touch-friendly controls */
button.lg { min-height: 58px !important; font-size: 1.15rem !important; border-radius: 14px !important; }
.ll-profile label { min-height: 44px; display: flex; align-items: center; }
.ll-profile input[type=checkbox] { width: 22px; height: 22px; }
"""


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
<div class="ll-sec"><h3>Ask the staff</h3><p><span class="ll-staff-it"><b>{esc(sp.get('it',''))}</b></span><br>{esc(sp.get('en',''))}</p></div>
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

with gr.Blocks(**blocks_kwargs) as demo:
    profile = gr.BrowserState(DEFAULT_PROFILE, storage_key="label_lens_profile")
    gr.Markdown("# Label Lens\nPhoto of an Italian label in, plain-English verdict out.")

    gr.HTML('<p class="ll-hint">1. Photograph the ingredients list, flat and well lit.</p>')
    img = gr.Image(sources=["upload", "webcam"], type="pil", label="Label photo",
                   height=320, **img_kwargs)
    go = gr.Button("Analyze label", variant="primary", elem_classes="lg")
    out = gr.HTML()

    summary = gr.Markdown(profile_summary([], [], []))
    with gr.Accordion("My diet profile (tap to edit)", open=False, elem_classes="ll-profile"):
        diets = gr.CheckboxGroup(DIETS, label="Diet")
        allergens = gr.CheckboxGroup(ALLERGENS, label="Allergens to avoid")
        goals = gr.CheckboxGroup(GOALS, label="Goals")

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