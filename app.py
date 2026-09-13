"""
SimplifyAI - Making Complex Documents Easy to Understand
Run with:  streamlit run app.py
"""

import html
import io
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

# Load .env (GROQ_API_KEY=..., TESSERACT_CMD=...) sitting next to this file.
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).with_name(".env"))
except ImportError:
    pass


def stored_api_key() -> str:
    """Look for the key in .env / environment, then Streamlit secrets."""
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(st.secrets["GROQ_API_KEY"]).strip()
    except Exception:
        return ""


MAX_CHARS = 12000
MODELS = ["openai/gpt-oss-120b", "qwen/qwen3.6-27b", "openai/gpt-oss-20b"]

# name -> (label shown on the tab, right-to-left script?)
LANGUAGES = {
    "Urdu": ("اردو", True),
    "Sindhi": ("سنڌي", True),
    "Punjabi (Shahmukhi)": ("پنجابی", True),
    "Pashto": ("پښتو", True),
    "Saraiki": ("سرائیکی", True),
    "Balochi": ("بلوچی", True),
    "Roman Urdu": ("Roman Urdu", False),
}
DATA_DIR = Path("simplifyai_data")
DATA_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="SimplifyAI", page_icon="◑", layout="wide",
                   initial_sidebar_state="expanded")

# ---------------------------------------------------------------- style
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&family=Noto+Nastaliq+Urdu:wght@400;700&display=swap');

:root {
  --ink:#0E1014; --surface:#15181F; --raised:#1B1F28; --line:#2A3040;
  --text:#E7E9EE; --muted:#8A93A6; --amber:#F2C14E; --teal:#5BD0B4;
  --rose:#F2735F; --violet:#9B8CFF;
}

#MainMenu, footer, header[data-testid="stHeader"] { visibility:hidden; }
.block-container { padding-top:2.2rem; max-width:1180px; }
html, body, [class*="st-"] { font-family:'Inter',sans-serif; }

/* keep Streamlit's Material icons on their own font, or ligatures
   render as literal text like "keyboard_arrow_right" */
[data-testid="stIconMaterial"],
[data-testid="stExpanderToggleIcon"],
span[class*="material-symbols"],
.material-symbols-rounded,
.material-symbols-outlined,
i.material-icons {
  font-family:'Material Symbols Rounded','Material Symbols Outlined','Material Icons'!important;
  font-feature-settings:'liga'!important;
  -webkit-font-feature-settings:'liga'!important;
  text-rendering:optimizeLegibility;
  letter-spacing:normal!important;
}

/* ---------- brand ---------- */
.sai-brand { display:flex; align-items:baseline; gap:.7rem; margin-bottom:.2rem; }
.sai-brand h1 {
  font-family:'Instrument Serif',serif; font-size:3.1rem; font-weight:400;
  letter-spacing:-.5px; color:var(--text); margin:0; line-height:1;
}
.sai-brand h1 em { font-style:italic; color:var(--amber); }
.sai-brand .rule { flex:1; height:1px; background:var(--line); }
.sai-tag {
  font-family:'JetBrains Mono',monospace; font-size:.68rem; letter-spacing:.16em;
  text-transform:uppercase; color:var(--muted); margin-bottom:2rem;
}

/* ---------- result cards ---------- */
.sai-result { margin-top:.5rem; }
.sai-hero {
  background:linear-gradient(135deg,#1A1F2B 0%,#15181F 100%);
  border:1px solid var(--line); border-left:3px solid var(--amber);
  border-radius:4px; padding:1.5rem 1.7rem; margin-bottom:1.1rem;
}
.sai-hero p { color:var(--text)!important; font-size:1.18rem; line-height:1.75; margin:.55rem 0 0; }
.eyebrow {
  font-family:'JetBrains Mono',monospace; font-size:.65rem; letter-spacing:.18em;
  text-transform:uppercase; color:var(--muted);
}
.sai-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(330px,1fr)); gap:1.1rem; }
.sai-card {
  background:var(--surface); border:1px solid var(--line); border-radius:4px;
  padding:1.25rem 1.4rem; position:relative;
}
.sai-card::before {
  content:""; position:absolute; left:0; top:1.25rem; bottom:1.25rem;
  width:2px; background:var(--accent,var(--line));
}
.sai-card.span { grid-column:1/-1; }
.t-amber  { --accent:var(--amber); }
.t-teal   { --accent:var(--teal); }
.t-rose   { --accent:var(--rose); }
.t-violet { --accent:var(--violet); }
.sai-card h3 {
  font-family:'Instrument Serif',serif; font-weight:400; font-size:1.35rem;
  color:var(--text); margin:.3rem 0 .9rem;
}
.sai-card ul { list-style:none; padding:0; margin:0; }
.sai-card li {
  color:var(--text); font-size:.95rem; line-height:1.65;
  padding:.42rem 0 .42rem 1.15rem; border-bottom:1px solid rgba(255,255,255,.04);
  position:relative;
}
.sai-card li:last-child { border-bottom:none; }
.sai-card li::before {
  content:"›"; position:absolute; left:0; color:var(--accent,var(--muted)); font-weight:600;
}
.sai-steps { counter-reset:step; }
.sai-steps li { padding-left:2.5rem; padding-top:.6rem; padding-bottom:.6rem; }
.sai-steps li::before {
  counter-increment:step; content:counter(step,decimal-leading-zero);
  font-family:'JetBrains Mono',monospace; font-size:.72rem;
  color:var(--ink); background:var(--accent,var(--muted));
  width:1.5rem; height:1.5rem; border-radius:50%;
  display:flex; align-items:center; justify-content:center; top:.55rem;
}

/* ---------- urdu ---------- */
.rtl { direction:rtl; text-align:right; }
.rtl .sai-hero { border-left:1px solid var(--line); border-right:3px solid var(--amber); }
.rtl .sai-card::before { left:auto; right:0; }
.rtl .sai-card li { padding-left:0; padding-right:1.15rem; }
.rtl .sai-card li::before { left:auto; right:0; content:"‹"; }
.rtl .sai-steps li { padding-right:2.5rem; }
.rtl .sai-steps li::before { left:auto; right:0; }
.rtl .sai-hero p, .rtl .sai-card li, .rtl .sai-card h3 {
  font-family:'Noto Nastaliq Urdu','Jameel Noori Nastaleeq','Noto Sans Arabic',serif;
  line-height:2.5;
}
.rtl .sai-hero p { font-size:1.1rem; }

/* ---------- history ---------- */
.sai-side-label {
  font-family:'JetBrains Mono',monospace; font-size:.63rem; letter-spacing:.16em;
  text-transform:uppercase; color:var(--muted); margin:1.3rem 0 .5rem;
}
section[data-testid="stSidebar"] { background:var(--surface); border-right:1px solid var(--line); }
section[data-testid="stSidebar"] button[kind="secondary"] {
  text-align:left; justify-content:flex-start; background:transparent;
  border:1px solid transparent; color:var(--text); font-size:.83rem; padding:.35rem .5rem;
}
section[data-testid="stSidebar"] button[kind="secondary"]:hover {
  background:var(--raised); border-color:var(--line); color:var(--amber);
}

/* ---------- ambient star field ---------- */
.sai-sky { position:fixed; inset:0; z-index:0; pointer-events:none; overflow:hidden; }
.sai-sky b {
  position:absolute; inset:-720px; display:block; background-repeat:repeat;
  will-change:transform;
}
.sai-sky .l1 {
  background-image:
    radial-gradient(2.2px 2.2px at 12% 18%, rgba(242,193,78,.95), transparent 62%),
    radial-gradient(1.8px 1.8px at 68% 9%,  rgba(255,255,255,.85), transparent 62%),
    radial-gradient(2.0px 2.0px at 33% 62%, rgba(242,193,78,.80), transparent 62%),
    radial-gradient(1.7px 1.7px at 84% 47%, rgba(255,255,255,.70), transparent 62%),
    radial-gradient(2.3px 2.3px at 51% 88%, rgba(242,193,78,.75), transparent 62%),
    radial-gradient(1.6px 1.6px at 7%  76%, rgba(255,255,255,.65), transparent 62%),
    radial-gradient(1.9px 1.9px at 44% 34%, rgba(255,255,255,.60), transparent 62%),
    radial-gradient(2.1px 2.1px at 92% 71%, rgba(242,193,78,.70), transparent 62%),
    radial-gradient(1.7px 1.7px at 22% 95%, rgba(255,255,255,.55), transparent 62%),
    radial-gradient(1.8px 1.8px at 76% 28%, rgba(242,193,78,.60), transparent 62%);
  background-size:360px 360px;
  animation:drift-a 110s linear infinite, twinkle-a 5.5s ease-in-out infinite;
}
.sai-sky .l2 {
  background-image:
    radial-gradient(1.5px 1.5px at 24% 41%, rgba(255,255,255,.70), transparent 62%),
    radial-gradient(1.7px 1.7px at 77% 24%, rgba(242,193,78,.75), transparent 62%),
    radial-gradient(1.4px 1.4px at 58% 71%, rgba(255,255,255,.55), transparent 62%),
    radial-gradient(1.6px 1.6px at 91% 83%, rgba(242,193,78,.60), transparent 62%),
    radial-gradient(1.3px 1.3px at 41% 14%, rgba(255,255,255,.50), transparent 62%),
    radial-gradient(1.5px 1.5px at 9%  58%, rgba(242,193,78,.55), transparent 62%),
    radial-gradient(1.4px 1.4px at 66% 93%, rgba(255,255,255,.45), transparent 62%);
  background-size:250px 250px;
  animation:drift-b 70s linear infinite, twinkle-b 3.8s ease-in-out infinite;
}
.sai-sky .l3 {
  background-image:
    radial-gradient(1.1px 1.1px at 15% 55%, rgba(255,255,255,.45), transparent 62%),
    radial-gradient(1.2px 1.2px at 63% 33%, rgba(242,193,78,.50), transparent 62%),
    radial-gradient(1.0px 1.0px at 88% 66%, rgba(255,255,255,.38), transparent 62%),
    radial-gradient(1.1px 1.1px at 37% 92%, rgba(255,255,255,.40), transparent 62%),
    radial-gradient(1.0px 1.0px at 72% 12%, rgba(242,193,78,.35), transparent 62%);
  background-size:170px 170px;
  animation:drift-c 45s linear infinite, twinkle-c 7.2s ease-in-out infinite;
}
@keyframes drift-a { to { transform:translate3d(-360px,360px,0); } }
@keyframes drift-b { to { transform:translate3d(250px,-250px,0); } }
@keyframes drift-c { to { transform:translate3d(-170px,-170px,0); } }
@keyframes twinkle-a { 0%,100%{opacity:.85} 50%{opacity:.35} }
@keyframes twinkle-b { 0%,100%{opacity:.45} 50%{opacity:.95} }
@keyframes twinkle-c { 0%,100%{opacity:.70} 50%{opacity:.25} }
.block-container, section[data-testid="stSidebar"] { position:relative; z-index:1; }

/* ---------- intro sequence ---------- */
.sai-intro {
  position:fixed; inset:0; z-index:9999; pointer-events:none;
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  background:radial-gradient(ellipse at center, #161A22 0%, #0E1014 70%);
  animation:intro-out .9s ease-in 5.6s forwards;
}
.sai-intro-title {
  font-family:'Instrument Serif',serif; font-weight:400; color:#FFFFFF;
  font-size:clamp(2.8rem,9vw,6.5rem); line-height:1; letter-spacing:-.02em;
  opacity:0; filter:blur(14px); transform:translateY(18px);
  animation:title-in 1.5s cubic-bezier(.2,.7,.3,1) .25s forwards;
}
.sai-intro-title em { font-style:italic; color:#F2C14E; }
.sai-intro-rule {
  height:1px; width:min(420px,62vw); margin:1.5rem 0 1.3rem;
  background:linear-gradient(90deg,transparent,#F2C14E,transparent);
  transform:scaleX(0); animation:rule-in 1.1s cubic-bezier(.2,.7,.3,1) 1.5s forwards;
}
.sai-intro-tag {
  font-family:'JetBrains Mono',monospace; color:#E7E9EE;
  font-size:clamp(.62rem,1.9vw,.86rem); letter-spacing:.28em; text-transform:uppercase;
  text-align:center; opacity:0; transform:translateY(14px);
  animation:tag-in 1.4s cubic-bezier(.2,.7,.3,1) 2.1s forwards;
}
.sai-intro-sub {
  font-family:'Inter',sans-serif; color:#8A93A6; font-size:.82rem;
  margin-top:1.1rem; opacity:0; animation:tag-in 1.3s ease-out 3.2s forwards;
}
.sai-intro-glow {
  position:absolute; width:520px; height:520px; border-radius:50%;
  background:radial-gradient(circle,rgba(242,193,78,.16) 0%,transparent 65%);
  opacity:0; animation:glow-in 2.4s ease-out .2s forwards;
}
@keyframes title-in { to { opacity:1; filter:blur(0); transform:translateY(0);} }
@keyframes rule-in  { to { transform:scaleX(1);} }
@keyframes tag-in   { to { opacity:1; transform:translateY(0);} }
@keyframes glow-in  { 0%{opacity:0;transform:scale(.7)} 60%{opacity:1} 100%{opacity:.75;transform:scale(1)} }
@keyframes intro-out { to { opacity:0; visibility:hidden;} }
@media (prefers-reduced-motion:reduce) {
  .sai-sky, .sai-intro { display:none; }
}

/* ---------- mobile ---------- */
@media (max-width:760px) {
  .block-container { padding:1rem .85rem 3rem!important; }
  .sai-brand h1 { font-size:2.3rem; }
  .sai-brand .rule { display:none; }
  .sai-tag { font-size:.56rem; letter-spacing:.1em; margin-bottom:1.2rem; }
  .sai-grid { grid-template-columns:1fr; gap:.8rem; }
  .sai-hero { padding:1.1rem 1.15rem; }
  .sai-hero p { font-size:1.02rem; line-height:1.65; }
  .sai-card { padding:1rem 1.05rem; }
  .sai-card h3 { font-size:1.18rem; }
  .sai-card li { font-size:.9rem; padding-top:.5rem; padding-bottom:.5rem; }
  .sai-steps li { padding-left:2.2rem; }
  .rtl .sai-steps li { padding-right:2.2rem; padding-left:0; }
  .rtl .sai-hero p { font-size:1rem; line-height:2.2; }
  .stTabs [data-baseweb="tab-list"] { gap:1.1rem; }
  .stTabs [data-baseweb="tab"] { font-size:.66rem; }
  .sai-sky .l3 { display:none; }           /* lighter animation load */
  .sai-intro-tag { letter-spacing:.16em; padding:0 1.4rem; line-height:1.9; }
  .sai-intro-rule { margin:1.1rem 0 1rem; }
}

/* ---------- widgets ---------- */
button[kind="primary"] {
  background:var(--amber)!important; color:#14161B!important; border:none!important;
  font-weight:600!important; letter-spacing:.02em; border-radius:3px!important;
}
.stTabs [data-baseweb="tab-list"] { gap:1.6rem; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] {
  background:transparent; padding:0 0 .6rem; font-family:'JetBrains Mono',monospace;
  font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; color:var(--muted);
}
.stTabs [aria-selected="true"] { color:var(--amber)!important; }
div[data-testid="stFileUploader"] section {
  background:var(--surface); border:1px dashed var(--line); border-radius:4px;
}
.stTextArea textarea, .stTextInput input {
  background:var(--surface)!important; border:1px solid var(--line)!important; color:var(--text)!important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- ambient layers
st.markdown(
    '<div class="sai-sky"><b class="l1"></b><b class="l2"></b><b class="l3"></b></div>',
    unsafe_allow_html=True,
)

if not st.session_state.get("intro_played"):
    st.session_state["intro_played"] = True
    st.markdown(
        '<div class="sai-intro">'
        '<div class="sai-intro-glow"></div>'
        '<div class="sai-intro-title">Simplify<em>AI</em></div>'
        '<div class="sai-intro-rule"></div>'
        '<div class="sai-intro-tag">Making complex documents easy to understand</div>'
        '<div class="sai-intro-sub">Plain English · اردو · a checklist you can act on</div>'
        "</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------- saved documents
def list_records():
    records = []
    for path in DATA_DIR.glob("*.json"):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return sorted(records, key=lambda r: r.get("created", ""), reverse=True)


def save_record(result: dict, source: str) -> dict:
    record = {
        "id": uuid.uuid4().hex[:12],
        "created": datetime.now().isoformat(timespec="seconds"),
        "title": result.get("title") or result.get("doc_type") or "Untitled document",
        "doc_type": result.get("doc_type", ""),
        "source": source,
        "result": result,
    }
    (DATA_DIR / f"{record['id']}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return record


def delete_record(record_id: str):
    path = DATA_DIR / f"{record_id}.json"
    if path.exists():
        path.unlink()


# ---------------------------------------------------------------- text extraction
def tesseract_ready() -> bool:
    import shutil

    import pytesseract

    custom = st.session_state.get("tesseract_path", "").strip()
    if custom:
        pytesseract.pytesseract.tesseract_cmd = custom
        return os.path.isfile(custom)
    return shutil.which("tesseract") is not None


def ocr_image(image, lang: str) -> str:
    import pytesseract

    return pytesseract.image_to_string(image, lang=lang).strip()


def ocr_pdf(data: bytes, lang: str, dpi: int = 300) -> str:
    import fitz
    from PIL import Image

    pages = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        total = len(doc)
        progress = st.progress(0.0, text="Scanning pages...")
        for index, page in enumerate(doc):
            pix = page.get_pixmap(dpi=dpi)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            pages.append(ocr_image(image, lang))
            progress.progress((index + 1) / total, text=f"Scanning page {index + 1} of {total}...")
        progress.empty()
    return "\n".join(pages).strip()


def extract_text(uploaded_file, ocr_lang: str = "eng+urd") -> tuple:
    name = uploaded_file.name.lower()
    data = uploaded_file.read()

    if name.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")):
        from PIL import Image

        if not tesseract_ready():
            raise RuntimeError("TESSERACT_MISSING")
        return ocr_image(Image.open(io.BytesIO(data)), ocr_lang), "OCR (image)"

    if name.endswith(".pdf"):
        import fitz

        with fitz.open(stream=data, filetype="pdf") as doc:
            text = "\n".join(page.get_text() for page in doc).strip()
        if len(text) >= 120:
            return text, "text layer"
        if not tesseract_ready():
            raise RuntimeError("TESSERACT_MISSING")
        return ocr_pdf(data, ocr_lang), "OCR (scanned PDF)"

    if name.endswith(".docx"):
        import docx

        document = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs).strip(), "text layer"

    return data.decode("utf-8", errors="ignore").strip(), "text layer"


# ---------------------------------------------------------------- LLM
SYSTEM_PROMPT = """You are SimplifyAI, an accessibility assistant for people who struggle with \
official documents in Pakistan and South Asia.

You are given the raw text of a document: a government notice, a university policy, medical \
instructions, a legal/official letter, or a job advertisement.

Rules:
- Use very simple words. Short sentences. No jargon. If a technical term must appear, explain it.
- Never invent facts, dates, fees or requirements that are not in the document. If something \
important is missing, say so plainly.
- Dates, amounts and document names must be copied exactly as written.
- The {language} version must be natural everyday {language} as really spoken in Pakistan, not a \
word-for-word translation. Keep proper nouns, English document names (CNIC) and numbers as they \
are. Write it in the normal script used for {language}.
- "labels" are the section headings, written in {language} and nothing else. Each label must \
contain ONLY the heading in {language} — never any English word, never the name of the language, \
never a dash or an explanation. The seven labels are the {language} versions of: "What this \
means" (meaning), "Deadlines" (deadlines), "You need" (required_documents), "Your next steps" \
(action_checklist), "Key points" (key_points), "Be careful about" (warnings), and "Questions you \
should ask" (questions_to_ask).

Return ONLY a JSON object with exactly these keys:

{{
  "title": "3-6 word title naming this specific document",
  "doc_type": "short label, e.g. University admission notice",
  "what_this_means": "2-4 very simple English sentences on what this document means for the reader",
  "key_points": ["important facts, one per item"],
  "deadlines": ["date or time limit + what it is for; empty list if none stated"],
  "required_documents": ["things the reader must bring or upload; empty list if none"],
  "action_checklist": ["ordered, concrete steps the reader should take"],
  "questions_to_ask": ["questions the reader should ask the office, doctor or employer"],
  "warnings": ["anything easy to miss: non-refundable fees, penalties, conditions"],
  "translated": {{
    "language": "{language}",
    "labels": {{
      "meaning": "...", "deadlines": "...", "required_documents": "...",
      "action_checklist": "...", "key_points": "...", "warnings": "...",
      "questions_to_ask": "..."
    }},
    "what_this_means": "same explanation in simple {language}",
    "key_points": ["..."], "deadlines": ["..."], "required_documents": ["..."],
    "action_checklist": ["..."], "questions_to_ask": ["..."], "warnings": ["..."]
  }}
}}"""


def simplify(text: str, api_key: str, model: str, language: str = "Urdu") -> dict:
    from groq import Groq

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(language=language)},
            {"role": "user", "content": f"Document text:\n\n{text[:MAX_CHARS]}"},
        ],
    )
    result = json.loads(response.choices[0].message.content)
    result["language"] = language
    result["translated_rtl"] = LANGUAGES.get(language, ("", True))[1]
    return result


# ---------------------------------------------------------------- rendering
LABELS = {
    "en": {
        "meaning": "What this means",
        "deadlines": "Deadlines",
        "required_documents": "You need",
        "action_checklist": "Your next steps",
        "key_points": "Key points",
        "warnings": "Be careful about",
        "questions_to_ask": "Questions you should ask",
    },
    "fallback": {
        "meaning": "اس کا مطلب کیا ہے",
        "deadlines": "آخری تاریخ",
        "required_documents": "آپ کو کیا درکار ہے",
        "action_checklist": "آپ کے اگلے اقدامات",
        "key_points": "اہم باتیں",
        "warnings": "احتیاط کریں",
        "questions_to_ask": "یہ سوالات ضرور پوچھیں",
    },
}

SECTIONS = [
    ("action_checklist", "t-teal", True, True),
    ("deadlines", "t-amber", False, False),
    ("required_documents", "t-violet", False, False),
    ("warnings", "t-rose", False, False),
    ("key_points", "t-teal", False, False),
    ("questions_to_ask", "t-violet", False, False),
]


def translated_block(result: dict) -> dict:
    """The second-language half of a result, whatever language it is."""
    return result.get("translated") or result.get("urdu") or {}


def clean_label(value, english: str, language: str):
    """Drop leaked placeholder text like 'Key points - in Sindhi'."""
    value = str(value or "").strip()
    if not value or value.lower() == english.lower():
        return None
    lowered = value.lower()
    for marker in (f"- in {language.lower()}", f"– in {language.lower()}",
                   f"in {language.lower()}", f"({language.lower()})", language.lower()):
        if marker in lowered:
            value = value[:lowered.index(marker)].strip(" -–—:")
            break
    if not value or value.lower() == english.lower():
        return None
    return value


def label_set(result: dict, translated: bool) -> dict:
    if not translated:
        return LABELS["en"]
    language = result.get("language", "Urdu")
    # Urdu headings are a safe default only when the language IS Urdu.
    labels = dict(LABELS["fallback"] if language == "Urdu" else LABELS["en"])
    for key, value in (translated_block(result).get("labels") or {}).items():
        if key in labels:
            cleaned = clean_label(value, LABELS["en"].get(key, ""), language)
            if cleaned:
                labels[key] = cleaned
    return labels


def card_html(title: str, items, tone: str, span: bool, numbered: bool, index: int) -> str:
    clean = [html.escape(str(i)).strip() for i in (items or []) if str(i).strip()]
    if not clean:
        return ""
    body = "".join(f"<li>{i}</li>" for i in clean)
    classes = f"sai-card {tone}" + (" span" if span else "")
    ul_class = "sai-steps" if numbered else ""
    return (
        f'<div class="{classes}">'
        f'<div class="eyebrow">{index:02d} / {len(clean)} items</div>'
        f"<h3>{html.escape(title)}</h3>"
        f'<ul class="{ul_class}">{body}</ul>'
        "</div>"
    )


def render(result: dict, translated: bool):
    source = translated_block(result) if translated else result
    labels = label_set(result, translated)
    rtl = translated and result.get("translated_rtl", True)
    meaning = html.escape(str(source.get("what_this_means", "")))

    cards = ""
    for position, (key, tone, span, numbered) in enumerate(SECTIONS, start=1):
        cards += card_html(labels[key], source.get(key), tone, span, numbered, position)

    st.markdown(
        f'<div class="sai-result {"rtl" if rtl else ""}">'
        f'<div class="sai-hero"><div class="eyebrow">{html.escape(labels["meaning"])}</div>'
        f"<p>{meaning}</p></div>"
        f'<div class="sai-grid">{cards}</div></div>',
        unsafe_allow_html=True,
    )


def as_plain_text(result: dict) -> str:
    lines = [f"SimplifyAI - {result.get('title', 'Document')}", ""]
    lines += ["WHAT THIS MEANS", result.get("what_this_means", ""), ""]
    for key in ["deadlines", "required_documents", "action_checklist", "key_points",
                "warnings", "questions_to_ask"]:
        items = result.get(key) or []
        if items:
            lines.append(LABELS["en"][key].upper())
            lines += [f"- {i}" for i in items]
            lines.append("")

    other = translated_block(result)
    if other.get("what_this_means"):
        labels = label_set(result, True)
        lines += ["=" * 50, result.get("language", "Translation").upper(), "",
                  labels["meaning"], other["what_this_means"], ""]
        for key in ["deadlines", "required_documents", "action_checklist", "key_points",
                    "warnings", "questions_to_ask"]:
            items = other.get(key) or []
            if items:
                lines.append(labels[key])
                lines += [f"- {i}" for i in items]
                lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------- PDF export
FONT_DIRS = [
    Path("fonts"),
    Path("/usr/share/fonts"),
    Path(r"C:\Windows\Fonts"),
    Path("/Library/Fonts"),
    Path("/System/Library/Fonts"),
]
FONT_NAMES = ["notonaskharabic", "notonastaliq", "jameel", "tahoma", "arial unicode", "arial"]


def unicode_font():
    """Any TTF that can draw Arabic script. A .ttf in a local 'fonts' folder wins."""
    local = Path("fonts")
    if local.is_dir():
        for candidate in sorted(local.glob("*.ttf")):
            return candidate

    for directory in FONT_DIRS[1:]:
        if not directory.is_dir():
            continue
        try:
            files = list(directory.rglob("*.ttf"))
        except OSError:
            continue
        for wanted in FONT_NAMES:
            for path in files:
                if wanted in path.name.lower().replace("-", "").replace("_", ""):
                    return path
    return None


def build_pdf(result: dict) -> bytes:
    from fpdf import FPDF

    font_file = unicode_font()
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(True, margin=18)
    pdf.set_margins(18, 18, 18)
    pdf.add_page()

    if font_file:
        pdf.add_font("uni", "", str(font_file))
        family = "uni"
        try:
            pdf.set_text_shaping(True)   # harfbuzz: joins Arabic letters correctly
        except Exception:
            pass
    else:
        family = "Helvetica"

    def heading(text, size=13, color=(176, 132, 30), gap=2, align="L"):
        pdf.set_font(family, size=size)
        pdf.set_text_color(*color)
        pdf.multi_cell(0, 7, str(text), align=align, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(gap)

    def body(text, size=11, align="L"):
        pdf.set_font(family, size=size)
        pdf.set_text_color(30, 30, 34)
        pdf.multi_cell(0, 6.4, str(text), align=align, new_x="LMARGIN", new_y="NEXT")

    def section(title, items, align="L"):
        items = [str(i).strip() for i in (items or []) if str(i).strip()]
        if not items:
            return
        heading(title, size=12, align=align)
        for item in items:
            body(f"•  {item}" if align == "L" else f"{item}  •", align=align)
        pdf.ln(3)

    heading(result.get("title", "Document"), size=19, color=(20, 20, 24), gap=1)
    body(result.get("doc_type", ""), size=10)
    pdf.ln(5)

    labels = LABELS["en"]
    heading(labels["meaning"])
    body(result.get("what_this_means", ""))
    pdf.ln(3)
    for key in ["deadlines", "required_documents", "action_checklist", "key_points",
                "warnings", "questions_to_ask"]:
        section(labels[key], result.get(key))

    other = translated_block(result)
    if other.get("what_this_means") and font_file:
        pdf.add_page()
        align = "R" if result.get("translated_rtl", True) else "L"
        tl = label_set(result, True)
        heading(result.get("language", "Translation"), size=16, color=(20, 20, 24), align=align)
        heading(tl["meaning"], align=align)
        body(other["what_this_means"], align=align)
        pdf.ln(3)
        for key in ["deadlines", "required_documents", "action_checklist", "key_points",
                    "warnings", "questions_to_ask"]:
            section(tl[key], other.get(key), align=align)

    return bytes(pdf.output())


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown('<div class="sai-side-label">Library</div>', unsafe_allow_html=True)

    if st.button("＋  New document", use_container_width=True, type="primary"):
        st.session_state.pop("result", None)
        st.session_state.pop("current_id", None)
        st.rerun()

    query = st.text_input("Search", placeholder="Search saved documents", label_visibility="collapsed")

    records = list_records()
    if query.strip():
        needle = query.lower()
        records = [
            r for r in records
            if needle in json.dumps(r, ensure_ascii=False).lower()
        ]

    if not records:
        st.caption("Nothing saved yet." if not query.strip() else "No matches.")
    for record in records[:40]:
        open_col, delete_col = st.columns([6, 1])
        date = record["created"][5:10].replace("-", "/")
        with open_col:
            if st.button(f"{date}  ·  {record['title'][:34]}", key=f"o{record['id']}",
                         use_container_width=True):
                st.session_state["result"] = record["result"]
                st.session_state["current_id"] = record["id"]
                st.rerun()
        with delete_col:
            if st.button("✕", key=f"d{record['id']}"):
                delete_record(record["id"])
                if st.session_state.get("current_id") == record["id"]:
                    st.session_state.pop("result", None)
                st.rerun()

    st.markdown('<div class="sai-side-label">Settings</div>', unsafe_allow_html=True)
    with st.expander("Model and OCR"):
        api_key = stored_api_key()
        if api_key:
            st.caption(f"Groq key loaded from .env  ·  ...{api_key[-4:]}")
        else:
            api_key = st.text_input("Groq API key", type="password",
                                    help="Or put GROQ_API_KEY=... in a .env file next to app.py")
        model = st.selectbox("Model", MODELS)
        ocr_lang = st.selectbox("OCR language", ["eng+urd", "eng", "urd"])
        st.text_input("Tesseract path (Windows only)", key="tesseract_path",
                      value=os.environ.get("TESSERACT_CMD", ""),
                      placeholder=r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        st.caption("OCR ready" if tesseract_ready() else "Tesseract not found")

# ---------------------------------------------------------------- main
st.markdown(
    '<div class="sai-brand"><h1>Simplify<em>AI</em></h1><div class="rule"></div></div>'
    '<div class="sai-tag">Difficult documents → plain English · اردو · a checklist you can act on</div>',
    unsafe_allow_html=True,
)

records = list_records()
bar_new, bar_lib, _ = st.columns([1.4, 1.4, 3.2])
with bar_new:
    if st.button("＋  New document", use_container_width=True, key="top_new"):
        st.session_state.pop("result", None)
        st.session_state.pop("current_id", None)
        st.session_state["show_library"] = False
        st.rerun()
with bar_lib:
    if st.button(f"☰  Saved  ({len(records)})", use_container_width=True, key="top_lib"):
        st.session_state["show_library"] = not st.session_state.get("show_library", False)
        st.rerun()

if st.session_state.get("show_library"):
    st.markdown('<div class="eyebrow" style="margin:1.2rem 0 .5rem">Library</div>',
                unsafe_allow_html=True)
    if not records:
        st.caption("Nothing saved yet — simplify a document and it will appear here.")
    for record in records[:30]:
        open_col, delete_col = st.columns([9, 1])
        date = record["created"][:10]
        with open_col:
            if st.button(f"{date}   ·   {record['title']}   —   {record.get('doc_type', '')}",
                         key=f"m{record['id']}", use_container_width=True):
                st.session_state["result"] = record["result"]
                st.session_state["current_id"] = record["id"]
                st.session_state["show_library"] = False
                st.rerun()
        with delete_col:
            if st.button("✕", key=f"md{record['id']}"):
                delete_record(record["id"])
                if st.session_state.get("current_id") == record["id"]:
                    st.session_state.pop("result", None)
                st.rerun()
    st.markdown("<hr style='border-color:#2A3040;margin:1.4rem 0'>", unsafe_allow_html=True)

st.write("")

if "result" not in st.session_state:
    document_text = ""
    tab_upload, tab_paste = st.tabs(["Upload a file", "Paste text"])

    with tab_upload:
        uploaded = st.file_uploader(
            "PDF, DOCX, TXT — or a photo/scan",
            type=["pdf", "docx", "txt", "png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff"],
        )
        if uploaded:
            try:
                with st.spinner("Reading the document..."):
                    document_text, how = extract_text(uploaded, ocr_lang)
                if document_text:
                    st.success(f"Read {len(document_text):,} characters via {how}.")
                    with st.expander("Preview extracted text"):
                        st.text(document_text[:3000])
                else:
                    st.warning("No readable text found. Try a clearer scan, or paste the text.")
            except RuntimeError as exc:
                if str(exc) == "TESSERACT_MISSING":
                    st.error("This file is a scan and needs OCR, but Tesseract was not found. "
                             "Install it, then set the path under Settings.")
                else:
                    st.error(f"Could not read the file: {exc}")
            except Exception as exc:
                st.error(f"Could not read the file: {exc}")

    with tab_paste:
        pasted = st.text_area("Paste the notice, policy or instructions",
                              height=240, label_visibility="collapsed",
                              placeholder="Paste the document text here...")
        if pasted.strip():
            document_text = pasted.strip()

    st.write("")
    pick_col, button_col = st.columns([1, 2])
    with pick_col:
        language = st.selectbox("Explain in", list(LANGUAGES.keys()), index=0)
    with button_col:
        st.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
        go = st.button("Simplify this document", type="primary", use_container_width=True)

    if go:
        if not api_key:
            st.error("Add your Groq API key under Settings in the sidebar.")
        elif not document_text:
            st.error("Upload a file or paste some text first.")
        else:
            if len(document_text) > MAX_CHARS:
                st.info(f"Long document — using the first {MAX_CHARS:,} characters.")
            try:
                with st.spinner(f"Reading and simplifying into English and {language}..."):
                    result = simplify(document_text, api_key, model, language)
                record = save_record(result, uploaded.name if uploaded else "pasted text")
                st.session_state["result"] = result
                st.session_state["current_id"] = record["id"]
                st.rerun()
            except Exception as exc:
                st.error(f"Something went wrong: {exc}")
else:
    result = st.session_state["result"]
    st.markdown(
        f'<div class="eyebrow">{html.escape(result.get("doc_type", "Document"))}</div>'
        f'<h2 style="font-family:\'Instrument Serif\',serif;font-weight:400;'
        f'margin:.2rem 0 1.2rem;color:#E7E9EE;">{html.escape(result.get("title", ""))}</h2>',
        unsafe_allow_html=True,
    )

    language = result.get("language", "Urdu")
    tab_label = LANGUAGES.get(language, (language, True))[0]
    english_tab, other_tab = st.tabs(["Simple English", tab_label])
    with english_tab:
        render(result, translated=False)
    with other_tab:
        render(result, translated=True)

    st.write("")
    text_col, pdf_col, _ = st.columns([1, 1, 3])
    slug = "".join(c for c in result.get("title", "document") if c.isalnum() or c in " -_")[:40]
    with text_col:
        st.download_button("Download as text", data=as_plain_text(result).encode("utf-8"),
                           file_name=f"{slug}.txt", mime="text/plain",
                           use_container_width=True)
    with pdf_col:
        try:
            st.download_button("Download as PDF", data=build_pdf(result),
                               file_name=f"{slug}.pdf", mime="application/pdf",
                               use_container_width=True)
        except Exception as exc:
            st.button("PDF failed", disabled=True, use_container_width=True)
            st.caption(f"PDF error: {exc}")