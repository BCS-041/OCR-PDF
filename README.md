
# 🏥 Prescription Parser

This script extracts **structured patient & prescription details** from **handwritten or printed doctor prescriptions**.
It supports **images (JPG/PNG)** and **multi-page PDFs**.

---

## 🚀 Features

* ✅ Supports **JPG / PNG / PDF** inputs
* ✅ OCR preprocessing for **better text recognition**
* ✅ Intelligent parsing with **LLM (via OpenRouter)**
* ✅ Normalizes drug names while **preserving suffixes (XR, DS, Plus, etc.)**
* ✅ Handles **common OCR errors** with smart corrections
* ✅ Outputs clean **structured JSON**

---

## 📦 Requirements

Install dependencies:

```bash
pip install pytesseract pillow requests pdf2image
```

🔹 System dependencies:

* **Tesseract OCR** (must be installed & added to PATH)
* **Poppler** (required for PDF → image conversion)

---

## ⚙️ Configuration

Edit these values in the script:

```python
OPENROUTER_API_KEY = ""   # 🔑 Add your OpenRouter API key
MODEL_NAME = "google/gemini-2.5-flash"
INPUT_FILE = "prescriptions.json"           # Input JSON with prescription URLs
OUTPUT_FILE = "extracted_prescriptions_v4.json"   # Parsed output file
```

---

## 📂 Input Format

`prescriptions.json` should contain a list of objects with prescription URLs:

```json
[
  { "url": "https://example.com/prescription1.jpg" },
  { "url": "https://example.com/prescription2.pdf" }
]
```

---

## 🖼️ Workflow

flowchart TD
    A[📥 Prescription URL <br/>(JPG / PNG / PDF)] --> B[🖼️ OCR Preprocessing]
    B --> C[🔎 Text Extraction <br/>(pytesseract / pdf2image)]
    C --> D[🤖 Parse with LLM <br/>(OpenRouter)]
    D --> E[💊 Normalize Medicines <br/>+ Patient Data]
    E --> F[📂 Structured JSON Output]
    F --> G[💾 Save to extracted_prescriptions_v4.json]

    %% 🎨 Styles
    style A fill:#ffdddd,stroke:#e63946,stroke-width:2px,color:#000
    style B fill:#ffe5b4,stroke:#f4a261,stroke-width:2px,color:#000
    style C fill:#f1faee,stroke:#457b9d,stroke-width:2px,color:#000
    style D fill:#d8f3dc,stroke:#2d6a4f,stroke-width:2px,color:#000
    style E fill:#fef9c3,stroke:#e9c46a,stroke-width:2px,color:#000
    style F fill:#e0bbff,stroke:#7b2cbf,stroke-width:2px,color:#000
    style G fill:#caffbf,stroke:#2a9d8f,stroke-width:2px,color:#000


---

## 📊 Example Output

```json
{
  "prescription_number": 1,
  "url": "https://example.com/prescription1.jpg",
  "parsed_output": {
    "Patient_Name": "Ram",
    "Age": 25,
    "Sex": "M",
    "Prescription_Date": "2025-09-14",
    "Vitals": {
      "Weight": null,
      "Height": null,
      "Temperature": null,
      "SpO2": null,
      "BP": "130/80",
      "Pulse_Rate": null
    },
    "Medicines": [
      {
        "Drug_Name": "Nexito 5 mg",
        "Dosage": "1 tab",
        "Frequency": "Once daily",
        "Duration": "30 days",
        "Notes": null
      }
    ],
    "Diagnostic_Tests": ["Blood Sugar", "Lipid Profile"],
    "Doctor_Name": "Dr. Sanjay Kumar",
    "Specialization": "Physician"
  }
}
```

---

## ▶️ Run

```bash
python prescription_parser.py
```

Output will be saved in:

```
extracted_prescriptions_v4.json
```
