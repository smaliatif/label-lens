import html
from pathlib import Path
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
VERDICT_ICON = {"OK": "&#10003;", "CHECK": "!", "AVOID": "&#10005;"}

ASSET_DIR = Path(__file__).parent
CSS = (ASSET_DIR / "styles.css").read_text(encoding="utf-8")
JS_SOURCE = (ASSET_DIR / "app.js").read_text(encoding="utf-8")
JS = f"() => {{\n{JS_SOURCE}\nwindow.LabelLensUI.init();\n}}"

# Mobile browser chrome matches the dark UI
HEAD = '<meta name="theme-color" content="#0d1310"><meta name="color-scheme" content="dark">'

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
    staff_phrase = sp.get("en", "")
    return f"""<div class="ll-card">
{retake}
<div class="ll-verdict ll-{v}" role="status"><div class="ll-verdict-icon" aria-hidden="true">{VERDICT_ICON[v]}</div><span class="ll-eyebrow">Label Lens verdict</span><h2>{v}</h2><p>{esc(r.get('product_name') or 'Unknown product')}</p>{reasons}</div>
<div class="ll-sec"><h3>Allergens detected</h3>{chips(r.get('allergens_detected', []))}
<p><small>Allergens not listed here were not detected on this label.</small></p></div>
<div class="ll-sec ll-notice">{NOTICE}</div>
<div class="ll-sec"><h3>Ingredients (English)</h3>{chips(r.get('ingredients_en', []))}</div>
<div class="ll-sec"><h3>Learn the words</h3><ul>{vocab}</ul></div>
<div class="ll-sec ll-staff"><h3>Ask the staff</h3><p><b>{esc(sp.get('it',''))}</b><br>{esc(staff_phrase)}</p>
<button type="button" class="ll-copy-button" data-copy-text="{html.escape(staff_phrase, quote=True)}">Copy question</button></div>
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

with gr.Blocks(title="Label Lens", css=CSS, js=JS, head=HEAD, theme=gr.themes.Base()) as demo:
    profile = gr.BrowserState(DEFAULT_PROFILE, storage_key="label_lens_profile")
    gr.HTML("""
        <header class="ll-header" id="top">
            <a class="ll-brand" href="#top" aria-label="Label Lens home">
                <span class="ll-brand-mark" aria-hidden="true">LL</span>
                <span><strong>label lens</strong><small>Italian labels, made clear</small></span>
            </a>
            <button class="ll-menu-toggle" type="button" aria-expanded="false" aria-controls="ll-nav" aria-label="Open navigation">
                <span></span><span></span><span></span>
            </button>
            <nav class="ll-nav" id="ll-nav" aria-label="Main navigation">
                <a href="#scan-panel">Scan a label</a><a href="#profile-panel">Your profile</a>
                <button type="button" class="ll-nav-safety" data-dialog-open="ll-safety-dialog">Safety note</button>
            </nav>
        </header>
        <section class="ll-intro">
            <p class="ll-kicker">A little more clarity at the table</p>
            <h1>Know what&rsquo;s on the label.</h1>
            <p>Photograph an Italian food label. Get a plain-English verdict, ingredients and the right words to ask.</p>
        </section>
        <dialog class="ll-dialog" id="ll-safety-dialog" aria-labelledby="ll-dialog-title">
            <div class="ll-dialog-inner">
                <button type="button" class="ll-dialog-close" data-dialog-close aria-label="Close safety note">Close</button>
                <p class="ll-kicker">Important</p><h2 id="ll-dialog-title">Use the package as your source of truth.</h2>
                <p>Label Lens is an aid, not medical advice. If you have an allergy, always check the physical package and ask the manufacturer or staff.</p>
            </div>
        </dialog>
        """)
    gr.HTML('<div class="ll-toast" id="ll-toast" role="status" aria-live="polite"></div>')
    with gr.Row(elem_classes="ll-workspace"):
        with gr.Column(scale=7, min_width=280, elem_id="scan-panel", elem_classes="ll-panel ll-scan-panel"):
            gr.HTML('<div class="ll-panel-heading"><h2>Scan the label</h2><p>Use a clear, well-lit photo of the ingredients.</p></div>')
            img = gr.Image(sources=["upload", "webcam"], type="pil", label="Label photo", height=300, elem_id="scan-image")
            go = gr.Button("Analyze label", variant="primary", elem_classes="ll-button", elem_id="analyze-btn")
        with gr.Column(scale=5, min_width=280, elem_id="profile-panel", elem_classes="ll-panel ll-profile-panel"):
            gr.HTML('<div class="ll-panel-heading"><h2>Your food profile</h2><p>Saved in this browser for your next scan.</p></div>')
            # Closed by default: on a phone the results stay close to the Analyze button
            with gr.Accordion("Diet and preferences", open=False, elem_id="profile-accordion"):
                diets = gr.CheckboxGroup(DIETS, label="Diet")
                allergens = gr.CheckboxGroup(ALLERGENS, label="Allergens to avoid")
                goals = gr.CheckboxGroup(GOALS, label="Goals")
    gr.HTML('<section class="ll-results-heading" id="results-heading"><h2>What&rsquo;s inside</h2></section>')
    out = gr.HTML(elem_id="results")
    gr.HTML('<footer class="ll-footer"><span class="ll-brand-mark" aria-hidden="true">LL</span><span>Label Lens <small>Read clearly. Choose confidently.</small></span></footer>')

    for c in (diets, allergens, goals):
        c.change(save_profile, [diets, allergens, goals], profile)
    demo.load(load_profile, profile, [diets, allergens, goals])
    go.click(run, [img, profile], out)

if __name__ == "__main__":
<<<<<<< HEAD
    demo.launch(server_name="0.0.0.0")
=======
    demo.launch(server_name="0.0.0.0", css=CSS, share=True)
>>>>>>> 66f706b0b3a33fb4c90aabdc322bd3ccdcb429d4
