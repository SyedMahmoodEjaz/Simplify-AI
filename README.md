# SimplifyAI

**Making complex documents easy to understand.**

SimplifyAI is a Generative AI accessibility tool that turns confusing official documents into clear, actionable information in the reader's own language.

Millions of people in Pakistan receive documents they cannot act on: a university admission notice full of clauses, a prescription written in medical shorthand, a government notification, a job advertisement with unstated conditions. The information is technically available but practically unreachable. The barrier is not literacy alone — it is language, jargon, and structure.

SimplifyAI takes that document and answers the questions the reader actually has: *What does this mean for me? What do I need? What do I do next? What should I watch out for? What should I ask?*

---

## What it does

Upload a PDF, Word file, or a **photo of a printed notice** — or just paste the text. SimplifyAI returns:

| Output | Purpose |
|---|---|
| **What this means** | A 2–4 sentence plain-language explanation |
| **Your next steps** | A numbered, concrete action checklist |
| **Deadlines** | Dates and time limits, copied exactly |
| **You need** | Documents to bring or upload |
| **Be careful about** | Non-refundable fees, penalties, hidden conditions |
| **Key points** | The facts worth remembering |
| **Questions you should ask** | What to ask the office, doctor, or employer |

Every section is produced twice: once in simple English, once in the reader's chosen language.

### Example

Instead of a paragraph of admission policy, the reader sees:

> **What this means:** You can apply for the BS morning program before 22 September 2026. The fee is Rs 1,500.
>
> **You need:** CNIC or Form B · Passport-size photograph · Intermediate marksheet
>
> **Your next steps:** 01 Fill the online form → 02 Upload your documents → 03 Pay the fee at the bank
>
> **Be careful about:** The fee is non-refundable. Incomplete applications are rejected without notice.

---

## Languages

Because "plain English" is still a barrier for many readers, the explanation can be delivered in:

**Urdu · Sindhi · Punjabi (Shahmukhi) · Pashto · Saraiki · Balochi · Roman Urdu**

The section headings are translated too, so the entire page reads in the chosen language rather than mixing scripts. Right-to-left layout is mirrored properly — the numbered steps, bullet markers, and card rules all flip.

---

## Accessibility features

- **OCR for scanned documents.** Most official notices in Pakistan circulate as photographs or scans with no text layer. SimplifyAI detects this automatically and runs OCR (English + Urdu) instead of failing silently.
- **Photo upload.** A reader can point a phone camera at a notice and upload the picture directly.
- **Download as PDF or text.** The simplified version can be saved, printed, or forwarded on WhatsApp to someone who needs it.
- **Document library.** Every result is saved locally and searchable, so a user can return to a notice weeks later without re-processing it.
- **Never invents facts.** The model is instructed to copy dates, amounts, and document names exactly, and to state plainly when required information is missing from the source rather than filling the gap.

---

## Sustainable Development Goals

| Goal | Contribution |
|---|---|
| **SDG 4 — Quality Education** | Makes admission notices, scholarship rules, and university policies understandable to first-generation students and their parents |
| **SDG 10 — Reduced Inequalities** | Removes the language and literacy barrier that keeps people from accessing services they are already entitled to |
| **SDG 3 — Good Health** | Explains prescriptions and medical instructions in the patient's own language |
| **SDG 16 — Strong Institutions** | Helps citizens understand and act on government communication |

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Interface | **Streamlit** | Fast to build, runs on desktop and mobile browsers |
| AI | **Groq API** (`openai/gpt-oss-120b`) | Free tier, very fast inference, JSON mode for structured output |
| Text extraction | **PyMuPDF**, **python-docx** | Reads the text layer where one exists |
| OCR | **Tesseract** + **pytesseract** | Handles scans and photographs, English and Urdu |
| PDF export | **fpdf2** + **uharfbuzz** | HarfBuzz shaping so Arabic-script letters join correctly |
| Storage | **JSON files** | No server, no account, nothing leaves the machine except the document text |

The model is asked for a strict JSON schema rather than prose, which is what makes the output reliably renderable as cards, checklists, and a printable PDF.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Tesseract (for scanned documents)

Optional — the app works without it, but scanned PDFs and photos will not.

- **Windows:** installer at [github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki) — tick **Urdu** under additional language data
- **Ubuntu / WSL:** `sudo apt install tesseract-ocr tesseract-ocr-urd`
- **macOS:** `brew install tesseract tesseract-lang`

### 3. Add your API key

Get a free key at [console.groq.com](https://console.groq.com). Copy `.env.example` to `.env` and fill it in:

```
GROQ_API_KEY=gsk_your_key_here
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

`TESSERACT_CMD` is only needed on Windows if Tesseract is not on your PATH.

### 4. Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. The terminal also prints a Network URL you can open on a phone connected to the same WiFi.

---

## Project structure

```
SimplifyAI/
├── app.py                  # The entire application
├── requirements.txt
├── .env                    # Your API key (not committed)
├── .env.example            # Template
├── .streamlit/
│   └── config.toml         # Dark theme
├── fonts/                  # Optional: drop a .ttf here for nicer Urdu PDFs
└── simplifyai_data/        # Saved documents (not committed)
```

---

## Notes and limitations

- **Translation quality varies by language.** Urdu and Sindhi are strong. Pashto, Saraiki, and Balochi have far less training data and should be checked before relying on them.
- **Long documents are truncated** to the first 12,000 characters.
- **OCR accuracy depends on scan quality.** A straight, well-lit photograph works well; a blurred or skewed one does not.
- **PDF export needs an Arabic-capable font.** Tahoma or Arial are found automatically on Windows. On other systems, place any suitable `.ttf` in a `fonts/` folder.
- **This is an aid, not an authority.** Users should verify deadlines and requirements against the original document. The app is designed to make the original readable, not to replace it.

---

## Deployment

To host it publicly on [Streamlit Community Cloud](https://share.streamlit.io):

1. Push this repository to GitHub
2. Connect it on Streamlit Cloud
3. Add `GROQ_API_KEY = "gsk_..."` under **Secrets** (the app reads `st.secrets` as a fallback)
4. For OCR, add a `packages.txt` file containing:
   ```
   tesseract-ocr
   tesseract-ocr-urd
   ```

---

## License

MIT
