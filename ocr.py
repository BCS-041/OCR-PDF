#This code is specifically created to fetch info from a doctor's handwritten prescription.
#This version supports prescriptions of all type e.g jpg/png/pdf
import os
import json
import base64
import requests
import pytesseract
from PIL import Image, ImageEnhance
from io import BytesIO
from pdf2image import convert_from_bytes
import re
from datetime import datetime
import demjson3  # pip install demjson3

# ---------------- CONFIG ----------------
OPENROUTER_API_KEY = ""  #Add your API KEY here
MODEL_NAME = "google/gemini-2.5-flash"
INPUT_FILE = "prescriptions.json" #fetch prescription url or pdf from here
OUTPUT_FILE = "extracted_prescriptions_clean.json"
IMAGES_FOLDER = "images" #fetch local image data from images folder

MASTER_PROMPT = """
You are an expert medical prescription parser with extensive experience in interpreting handwritten and printed prescriptions.

Use your medical knowledge to:

1. Understand all medical shorthand and abbreviations (OD, BD, TDS, QID, SOS, PRN, STAT, etc.) and expand them to human-readable form.
2. Normalize drug names and dosages like an experienced prescription reader.
3. Correct obvious OCR errors (e.g., l→1, O→0, I→1).
4. Extract Patient_Name, Age, Sex, Phone, Prescription_Date, Vitals, Diagnosis_Details, Medicines, Diagnostic_Tests, Doctor_Name, Specialization.
5. Include `Manual_QA_Flags` for any missing, suspicious, or potentially incorrect fields.
6. Do not include internal scoring or confidence values—only cleaned values and manual QA flags.
7. Output valid JSON only.
**Accuracy > completeness** — prefer null over incorrect data.

**Output JSON schema:**
{
  "Patient_Name": {"Value": "string or null"},
  "Age": "number or null",
  "Sex": "M|F|null",
  "Phone": "string or null",
  "Prescription_Date": "YYYY-MM-DD or null",
  "Vitals": {
    "Weight": "string or null",
    "Height": "string or null",
    "Temperature": "string or null",
    "SpO2": "string or null",
    "BP": "string or null",
    "Pulse_Rate": "string or null",
    "Respiratory_Rate": null,
    "Blood_Sugar": null,
    "BMI": null,
    "Waist_Circumference": null,
    "ECG": null,
    "Fasting_Blood_Sugar": null,
    "pH": null,
    "CBC": null
  },
  "Diagnosis_Details": "string or null",
  "Medicines": [
    {
      "Drug_Name": {"Value": "string or null"},
      "Dosage": "string or null",
      "Frequency": "string or null",
      "Duration": "string or null",
      "Notes": "string or null"
    }
  ],
  "Diagnostic_Tests": ["string"],
  "Doctor_Name": "string or null",
  "Specialization": "string or null",
  "Confidence_Level": {"Overall": "high|medium|low", "Reason": "string or null"},
  "Manual_QA_Flags": ["field names needing manual review"]
}
"""

# ---------------- IMAGE PREPROCESSING ----------------
def preprocess_image(image):
    image = image.convert('L')
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(3.0)
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.5)
    return image.point(lambda p: p > 150 and 255)

# ---------------- OCR ----------------
def extract_text_from_image_file(file_path: str) -> str:
    try:
        img = Image.open(file_path)
        processed = preprocess_image(img)
        return pytesseract.image_to_string(processed, config="--psm 6")
    except Exception as e:
        return f"ERROR: {e}"

def extract_text_from_pdf_file(file_path: str) -> str:
    try:
        if str(file_path).startswith("http"):
            r = requests.get(file_path, timeout=30)
            r.raise_for_status()
            pdf_bytes = r.content
        else:
            pdf_bytes = open(file_path, "rb").read()

        pages = convert_from_bytes(pdf_bytes)
        text = ""
        for page_num, page in enumerate(pages, start=1):
            processed = preprocess_image(page)
            page_text = pytesseract.image_to_string(processed, config="--psm 6")
            text += f"\n--- Page {page_num} ---\n{page_text}\n"
        return text.strip()
    except Exception as e:
        return f"ERROR: {e}"

# ---------------- BASE64 ENCODING ----------------
def encode_file_to_base64(file_identifier: str) -> list:
    try:
        if str(file_identifier).startswith("http"):
            r = requests.get(file_identifier, timeout=30)
            r.raise_for_status()
            ext = file_identifier.lower().split(".")[-1]
            if ext == "pdf":
                pages = convert_from_bytes(r.content)
                base64_list = []
                for page in pages:
                    buf = BytesIO()
                    page.save(buf, format="JPEG")
                    base64_list.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
                return base64_list
            else:
                return [base64.b64encode(r.content).decode("utf-8")]
        else:
            ext = file_identifier.lower().split(".")[-1]
            if ext == "pdf":
                pages = convert_from_bytes(open(file_identifier, "rb").read())
                base64_list = []
                for page in pages:
                    buf = BytesIO()
                    page.save(buf, format="JPEG")
                    base64_list.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
                return base64_list
            else:
                with open(file_identifier, "rb") as f:
                    return [base64.b64encode(f.read()).decode("utf-8")]
    except Exception as e:
        print(f"Encoding failed: {e}")
        return []

# ---------------- OPENROUTER CALL ----------------
def call_openrouter(ocr_text: str, file_identifier: str) -> dict:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    content = [
        {"type": "text", "text": MASTER_PROMPT},
        {"type": "text", "text": f"OCR Extracted Text:\n{ocr_text}"},
    ]

    for img in encode_file_to_base64(file_identifier):
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": MASTER_PROMPT},
            {"role": "user", "content": content}
        ],
        "max_tokens": 3000,
        "temperature": 0.0
    }

    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        response_json = r.json()
        if "choices" not in response_json or len(response_json["choices"]) == 0:
            return {"error": "No choices in response from OpenRouter"}

        response_text = response_json["choices"][0]["message"]["content"]
        clean = response_text.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            return demjson3.decode(clean)
        except Exception as e:
            return {"error": f"JSON decode error: {e}", "raw_response": clean}
    except Exception as e:
        return {"error": str(e)}

# ---------------- MAIN ----------------
def process_prescriptions():
    results = []

    # --- Step 1: process URLs from JSON ---
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            prescriptions = json.load(f)

        for idx, entry in enumerate(prescriptions, 1):
            url = entry.get("url")
            print(f"\n🔎 Processing URL {idx}: {url}")

            ext = url.lower().split(".")[-1]
            if ext == "pdf":
                ocr_text = extract_text_from_pdf_file(url)
            else:
                ocr_text = extract_text_from_image_file(url)

            parsed = call_openrouter(ocr_text, url)
            if "error" in parsed:
                print(f"⚠️ LLM failed for {url}, using OCR-only fallback")
                parsed = {
                    "Patient_Name": {"Value": None},
                    "Medicines": [],
                    "Manual_QA_Flags": ["LLM failed, use OCR-only"],
                    "Confidence_Level": {"Overall": "low", "Reason": "LLM failed"}
                }

            results.append({"prescription_number": idx, "source": url, "parsed_output": parsed})
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f" ✅ Completed URL {idx}")

    # --- Step 2: process local images in folder ---
    if os.path.exists(IMAGES_FOLDER):
        files = sorted(os.listdir(IMAGES_FOLDER))
        for idx, filename in enumerate(files, len(results)+1):
            file_path = os.path.join(IMAGES_FOLDER, filename)
            print(f"\n🔎 Processing local file {idx}: {filename}")

            ext = filename.lower().split(".")[-1]
            if ext == "pdf":
                ocr_text = extract_text_from_pdf_file(file_path)
            else:
                ocr_text = extract_text_from_image_file(file_path)

            parsed = call_openrouter(ocr_text, file_path)
            if "error" in parsed:
                print(f"⚠️ LLM failed for {filename}, using OCR-only fallback")
                parsed = {
                    "Patient_Name": {"Value": None},
                    "Medicines": [],
                    "Manual_QA_Flags": ["LLM failed, use OCR-only"],
                    "Confidence_Level": {"Overall": "low", "Reason": "LLM failed"}
                }

            results.append({"prescription_number": idx, "source": filename, "parsed_output": parsed})
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f" ✅ Completed local file {idx}")

    print(f"\n📊 All results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_prescriptions()
