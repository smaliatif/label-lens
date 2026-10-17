import html
import gradio as gr

#we have to change this line to fare cose with the frontend
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
.gradio-container { max-width: 520px !important; margin: 0 auto !important; }
.ll-card { font-family: system-ui, sans-serif; line-height: 1.45; }
.ll-verdict { border-radius: 14px; padding: 18px; color: #fff; margin-bottom: 14px; }
.ll-verdict h2 { margin: 0 0 4px; font-size: 1.9rem; color: #fff; }
.ll-verdict p { margin: 2px 0; color: #fff; }
.ll-OK { background: #1f7a4d; } .ll-CHECK { background: #a86a00; } .ll-AVOID { background: #b3261e; }
.ll-sec { margin: 14px 0; } .ll-sec h3 { margin: 0 0 6px; font-size: 1rem; }
.ll-chip { display: inline-block; padding: 4px 10px; margin: 2px 4px 2px 0;
           border-radius: 999px; background: rgba(128,128,128,.18); font-size: .9rem; }
.ll-notice { border-left: 4px solid #b3261e; padding: 8px 12px; background: rgba(179,38,30,.1); border-radius: 6px; }
.ll-retake { border: 2px dashed #a86a00; padding: 12px; border-radius: 10px; margin-bottom: 12px; }
button.lg { min-height: 52px !important; font-size: 1.05rem !important; }
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
<div class="ll-sec"><h3>Ask the staff</h3><p><b>{esc(sp.get('it',''))}</b><br>{esc(sp.get('en',''))}</p></div>
</div>"""

def run(image, profile):
    if image is None:
        raise gr.Error("Take or upload a photo of the label first.")
    try:
        return render(analyze(image, profile or DEFAULT_PROFILE))
    except Exception as e:
        raise gr.Error(f"Analysis failed: {e}")

def load_profile(profile):
    p = profile or DEFAULT_PROFILE
    return p["diets"], p["allergens"], p["goals"]

def save_profile(diets, allergens, goals):
    return {"diets": diets, "allergens": allergens, "goals": goals}

with gr.Blocks(title="Label Lens") as demo:
    profile = gr.BrowserState(DEFAULT_PROFILE, storage_key="label_lens_profile")
    gr.Markdown("# Label Lens\nPhoto of an Italian label in, plain-English verdict out.")
    with gr.Accordion("My diet profile", open=False):
        diets = gr.CheckboxGroup(DIETS, label="Diet")
        allergens = gr.CheckboxGroup(ALLERGENS, label="Allergens to avoid")
        goals = gr.CheckboxGroup(GOALS, label="Goals")
    img = gr.Image(sources=["upload", "webcam"], type="pil", label="Label photo", height=300)
    go = gr.Button("Analyze label", variant="primary", elem_classes="lg")
    out = gr.HTML()

    for c in (diets, allergens, goals):
        c.change(save_profile, [diets, allergens, goals], profile)
    demo.load(load_profile, profile, [diets, allergens, goals])
    go.click(run, [img, profile], out)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", css=CSS, share=True)
