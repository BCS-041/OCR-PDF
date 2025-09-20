#This code is specifically created to fetch info from a doctor's handwritten prescription.
#This version supports prescriptions of all type e.g jpg/png/pdf
import os
import json
import base64
import requests
import pytesseract
from PIL import Image, ImageEnhance
from io import BytesIO
from pdf2image import convert_from_bytes   # ✅ PDF support

# ---------------- CONFIG ----------------
OPENROUTER_API_KEY = "" #add your openrouter key
MODEL_NAME = "google/gemini-2.5-flash"
INPUT_FILE = "prescriptions.json"
OUTPUT_FILE = "extracted_prescriptions_v4.json"

# ---------------- STRICTER MASTER PROMPT ----------------
MASTER_PROMPT = """ 
You are an expert medical prescription parser with extensive experience in interpreting handwritten and printed prescriptions. Extract structured information from OCR text and/or images of prescriptions and return only valid JSON.

Output must follow this schema exactly:

{
"Patient_Name": "string or null",
"Age": "number or null",
"Sex": "M|F|null",
"Prescription_Date": "YYYY-MM-DD or null",
"Vitals": {
"Weight": "string or null",
"Height": "string or null",
"Temperature": "string or null",
"SpO2": "string or null",
"BP": "string or null",
"Pulse_Rate": "string or null"
},
"Medicines": [
{
"Drug_Name": "string (normalized BUT WITH SUFFIXES PRESERVED)",
"Dosage": "string or null",
"Frequency": "string or null",
"Duration": "string or null",
"Notes": "string or null"
}
],
"Diagnostic_Tests": ["string"],
"Doctor_Name": "string or null",
"Specialization": "string or null"
}

Rules:

Output ONLY JSON, no extra text or explanation.

Correct OCR errors intelligently using medical knowledge.

Normalize drug names but always preserve suffixes (F, XR, DS, SR, Plus, M, H, AP, XL, CR, ER).

Use null for missing or unreadable fields.

Do not confuse frequency notation like 1 OD / 1od with numeric 100.

Accuracy > completeness: prefer null over incorrect data.

Patient name corrections:
"Nachanana","Shahnaz","Shanara","Sahanaraa" → "Sahanara"
"Nachanana Bibi","Shahnaz Bibi" → "Sahanara Bibi"
"Goards","Gourds","Gauridas" → "Gauri Das"
"Kartlk","Kartiek","Karlick" → "Kartik"
"Amtt","Amiti" → "Amit"

Medicine normalization (examples, preserve suffixes):
"RozatF10/160","RozatF10-160" → "Rozat F 10/160"
"Nexito5","Nexito 5mg" → "Nexito 5 mg"
"Cyra20","Cyra 20mg" → "Cyra 20 mg"
"Allegra120" → "Allegra 120 mg"
"IstametXR" → "Istamet XR 10/1000"
"TelmikindH" → "Telmikind H 40/12.5"
"Meganeuron Pg","Meganuron Pq" → "Meganeuron PG"
"D Rise 60k","DRise60k" → "D-Rise 60k"
"Jointrium-M" → "Jointrium M"
"Chymoral-AP" → "Chymoral AP"
"Cyanocobalamine","Cyanocobal" → "Cyanocobalamin"
"Bandy+" → "Bandy Plus"
"Itrazole200" → "Itrazole 200 mg"
"Hetarzan100" → "Hetarzan 100 mg"
"Pantaprazole","Pantop" → "Pantoprazole"
"Paracetmol","Pcm" → "Paracetamol"
"Amoxycillin","Amox" → "Amoxicillin"
"Azithromycine","Azithro" → "Azithromycin"
"Atorvastin","Atorva" → "Atorvastatin"
"Metformln","Metf" → "Metformin"
"Amangly M" → "Amaryl M"
"Telma-AM H 100" → "Telma-AM H"
"Eltroxin 70/100" → "Eltroxin"
"xanttielen" → "Xanthelasma"
"Codcom-Plus" → "Cedon-Plus"
"Fosamax","Nospaz Forte" → "Myospaz Forte"
"Calcidon" → "Calcidol"
"Lorax 0.5" → "LOXOF OZ"
"Atorvastatin 20 mg" → "Stator 20"

Additional common medicines:
"Cefixime200","Cefixime 200" → "Cefixime 200 mg"
"CefuroximeAxetil500","Cefuroxime-500" → "Cefuroxime Axetil 500 mg"
"Ceftriaxone1g","Ceftriaxone 1 g" → "Ceftriaxone 1 g"
"Amox-Clav","Augmentin625","Augmentin 625" → "Amoxicillin-Clavulanate 625 mg"
"Amlodipine5","Amlodipine 5mg" → "Amlodipine 5 mg"
"Losartan50","Losartan 50mg" → "Losartan 50 mg"
"Lisinopril10" → "Lisinopril 10 mg"
"Clopidogrel75" → "Clopidogrel 75 mg"
"Warfarin5" → "Warfarin 5 mg"
"Levothyroxine50mcg","Eltroxin50" → "Levothyroxine 50 mcg"
"Omeprazole20","Rabeprazole20","Pantoprazole20" → normalize with strength
"Ondansetron4","Domperidone10","Metronidazole400","Fluconazole150","Itraconazole100","Levofloxacin500","Doxycycline100","Salbutamol Inhaler" → normalize to standard naming

Dosage/Frequency:
"od","o.d.","OD","1 OD","1od" → "Once daily"
"bd","b.d.","BD" → "Twice daily"
"tds","t.d.s.","TDS" → "Thrice daily"
"qid","q.i.d.","QID" → "Four times daily"
"hs","h.s.","HS" → "At bedtime"
"sos","s.o.s.","SOS" → "As needed"

Frequency special rule:
"100","1OO","I00","1O0","l00" → "1 OD" → "Once daily" (do not confuse with numeric 100 mg)
If unit follows (mg, mcg) treat as numeric strength.

Suffix preservation is mandatory:
Never remove suffixes F, XR, DS, SR, Plus, M, H, AP, XL, CR, ER.
Examples: "Metformin F" → "Metformin F", "Azithromycin Plus" → "Azithromycin Plus", "Pantoprazole DS" → "Pantoprazole DS"

Date normalization:
All dates → YYYY-MM-DD
Age normalization:
"30yrs","30 yrs","30Y" → 30, "45 years","45years" → 45

Context:
"Tab","Tabl","Caps","Cap","Inj" → tablet/capsule/injection
"Sig:" or "Directions:" → start of instructions

Special instructions:
Include all medicines in array even if fields are null.
Extract partially readable fields if possible.
Accuracy over completeness. Never guess or remove suffixes.
"""

# ---------------- IMAGE PREPROCESSING ----------------
def preprocess_image(image):
    """Enhance image for better OCR results"""
    image = image.convert('L')
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(3.0)
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.5)
    return image.point(lambda p: p > 150 and 255)

# ---------------- OCR FROM IMAGE ----------------
def extract_text_from_image(url: str) -> str:
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content))
        processed = preprocess_image(img)
        return pytesseract.image_to_string(processed, config="--psm 6")
    except Exception as e:
        return f"ERROR: {e}"

# ---------------- OCR FROM PDF (all pages) ----------------
def extract_text_from_pdf(url: str) -> str:
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        pdf_bytes = r.content
        pages = convert_from_bytes(pdf_bytes)

        text = ""
        for page_num, page in enumerate(pages, start=1):
            processed = preprocess_image(page)
            page_text = pytesseract.image_to_string(processed, config="--psm 6")
            text += f"\n--- Page {page_num} ---\n{page_text}\n"
        return text.strip()
    except Exception as e:
        return f"ERROR: {e}"

# ---------------- ENCODE IMAGE ----------------
def encode_image_to_base64(url: str) -> list:
    """Return list with a single base64 image (for images)"""
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return [base64.b64encode(r.content).decode("utf-8")]
    except Exception as e:
        print(f"Image encoding failed: {e}")
        return []

# ---------------- ENCODE PDF (all pages) ----------------
def encode_pdf_to_base64(url: str) -> list:
    """Return base64 list for ALL PDF pages"""
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        pages = convert_from_bytes(r.content)

        base64_list = []
        for page in pages:
            buf = BytesIO()
            page.save(buf, format="JPEG")
            base64_list.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
        return base64_list
    except Exception as e:
        print(f"PDF encoding failed: {e}")
        return []

# ---------------- CALL OPENROUTER ----------------
def call_openrouter(ocr_text: str, url: str) -> dict:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    content = [
        {"type": "text", "text": MASTER_PROMPT},
        {"type": "text", "text": f"OCR Extracted Text:\n{ocr_text}"},
    ]

    # Attach base64 previews
    base64_imgs = []
    if url.lower().endswith(".pdf"):
        base64_imgs = encode_pdf_to_base64(url)
    else:
        base64_imgs = encode_image_to_base64(url)

    for img in base64_imgs:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": MASTER_PROMPT},
            {"role": "user", "content": content}
        ],
        "max_tokens": 2000,
        "temperature": 0.0
    }

    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        response = r.json()["choices"][0]["message"]["content"]
        clean = response.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean)
    except Exception as e:
        return {"error": str(e)}

# ---------------- MAIN ----------------
def process_prescriptions():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        prescriptions = json.load(f)

    results = []
    for idx, entry in enumerate(prescriptions, 1):
        url = entry.get("url")
        print(f"\n🔎 Processing Prescription {idx}: {url}")

        # Auto-detect PDF vs Image
        if url.lower().endswith(".pdf"):
            ocr_text = extract_text_from_pdf(url)
        else:
            ocr_text = extract_text_from_image(url)

        parsed = call_openrouter(ocr_text, url)

        results.append({"prescription_number": idx, "url": url, "parsed_output": parsed})

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f" ✅ Completed prescription {idx}")

    print(f"\n📊 All results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_prescriptions()
