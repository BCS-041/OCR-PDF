import os
import json
import base64
import requests
import pytesseract
from PIL import Image, ImageEnhance
from io import BytesIO
from pdf2image import convert_from_bytes
import demjson3
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Prescription Parser API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- CONFIG ----------------
MODEL_NAME = "google/gemini-2.5-flash"
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
    "Respiratory_Rate": "string or null",
    "Blood_Sugar": "string or null",
    "BMI": "string or null",
    "Waist_Circumference": "string or null",
    "ECG": "string or null",
    "Fasting_Blood_Sugar": "string or null",
    "pH": "string or null",
    "CBC": "string or null"
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
    """Enhance image contrast and sharpness for better OCR results."""
    image = image.convert("L")
    image = ImageEnhance.Contrast(image).enhance(3.0)
    image = ImageEnhance.Sharpness(image).enhance(2.5)
    return image.point(lambda p: p > 150 and 255)

# ---------------- OCR ----------------
def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from image bytes."""
    try:
        img = Image.open(BytesIO(image_bytes))
        processed = preprocess_image(img)
        return pytesseract.image_to_string(processed, config="--psm 6")
    except Exception as e:
        return f"ERROR: {e}"

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes."""
    try:
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
def encode_image_to_base64(image_bytes: bytes) -> str:
    """Convert image bytes to base64."""
    return base64.b64encode(image_bytes).decode('utf-8')

# ---------------- OPENROUTER CALL ----------------
def call_openrouter(ocr_text: str, image_base64: str, api_key: str) -> dict:
    """Send OCR + image data to OpenRouter and parse structured JSON response."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    content = [
        {"type": "text", "text": MASTER_PROMPT},
        {"type": "text", "text": f"OCR Extracted Text:\n{ocr_text}"},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
    ]

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": MASTER_PROMPT},
            {"role": "user", "content": content}
        ],
        "max_tokens": 3000,
        "temperature": 0.0,
    }

    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        response_json = r.json()

        if "choices" not in response_json or not response_json["choices"]:
            return {"error": "No choices in response from OpenRouter"}

        response_text = response_json["choices"][0]["message"]["content"]
        clean = response_text.strip().removeprefix("```json").removesuffix("```").strip()

        try:
            return demjson3.decode(clean)
        except Exception as e:
            return {"error": f"JSON decode error: {e}", "raw_response": clean}

    except Exception as e:
        return {"error": str(e)}

# ---------------- API ENDPOINTS ----------------
@app.get("/")
async def root():
    return {"message": "Prescription Parser API", "status": "healthy"}

@app.post("/parse-prescription")
async def parse_prescription(
    file: UploadFile = File(...),
    api_key: str = Form(None)
):
    """Parse a prescription image or PDF."""
    
    # Use provided API key or environment variable
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenRouter API key required")
    
    # Read file content
    contents = await file.read()
    file_extension = file.filename.split('.')[-1].lower()
    
    try:
        # Extract text based on file type
        if file_extension == 'pdf':
            ocr_text = extract_text_from_pdf(contents)
        else:
            ocr_text = extract_text_from_image(contents)
        
        # Encode image for LLM
        image_base64 = encode_image_to_base64(contents)
        
        # Call OpenRouter
        result = call_openrouter(ocr_text, image_base64, api_key)
        
        return JSONResponse(content={
            "filename": file.filename,
            "ocr_text": ocr_text,
            "parsed_prescription": result
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# For local development
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
