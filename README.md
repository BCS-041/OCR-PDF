# 🏥 Prescription Parser

This script extracts **structured patient & prescription details** from **handwritten or printed doctor prescriptions**. It supports **images (JPG/PNG)** and **multi-page PDFs**.

![Python](https://img.shields.io/badge/Python-3.13%2B-blue)
![OCR](https://img.shields.io/badge/OCR-Tesseract-green)
![LLM](https://img.shields.io/badge/LLM-OpenRouter-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 🚀 Features

- ✅ Supports **JPG / PNG / PDF** inputs
- ✅ OCR preprocessing for **better text recognition**
- ✅ Intelligent parsing with **LLM (via OpenRouter)**
- ✅ Normalizes drug names while **preserving suffixes (XR, DS, Plus, etc.)**
- ✅ Handles **common OCR errors** with smart corrections
- ✅ Outputs clean **structured JSON**

---

## 📦 Installation & Requirements

### Python Dependencies
```bash
pip install pytesseract pillow requests pdf2image
```

### System Dependencies
- **Tesseract OCR** (must be installed & added to PATH)
- **Poppler** (required for PDF → image conversion)

#### Installation on Ubuntu/Debian:
```bash
sudo apt update
sudo apt install tesseract-ocr poppler-utils
```

#### Installation on macOS:
```bash
brew install tesseract poppler
```

#### Installation on Windows:
Download and install:
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
- [Poppler for Windows](http://blog.alivate.com.au/poppler-windows/)

---

## ⚙️ Configuration

Edit these values in the script:

```python
OPENROUTER_API_KEY = ""   # 🔑 Add your OpenRouter API key
MODEL_NAME = "google/gemini-2.5-flash"
INPUT_FILE = "prescriptions.json"           # Input JSON with prescription URLs
OUTPUT_FILE = "extracted_prescriptions_v4.json"   # Parsed output file
```

> **Note**: You need to obtain an API key from [OpenRouter](https://openrouter.ai/) to use this tool.

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

```mermaid
flowchart TD
    A[📥 Prescription URL<br/>(JPG / PNG / PDF)] --> B[🖼️ OCR Preprocessing]
    B --> C[🔎 Text Extraction<br/>(pytesseract / pdf2image)]
    C --> D[🤖 Parse with LLM<br/>(OpenRouter)]
    D --> E[💊 Normalize Medicines<br/>+ Patient Data]
    E --> F[📂 Structured JSON Output]
    F --> G[💾 Save to extracted_prescriptions_v4.json]
```

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

## ▶️ Usage

1. Prepare your `prescriptions.json` file with prescription URLs
2. Configure the script with your OpenRouter API key
3. Run the parser:

```bash
python prescription_parser.py
```

4. Output will be saved to: `extracted_prescriptions.json`

---

## 🐛 Troubleshooting

### Common Issues:

1. **Tesseract not found error**
   - Ensure Tesseract OCR is installed and added to your system PATH
   - On Windows, you may need to specify the Tesseract path in code:
     ```python
     pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
     ```

2. **PDF conversion issues**
   - Verify Poppler is installed correctly
   - On Windows, add Poppler to your PATH or specify the path in code

3. **API errors**
   - Verify your OpenRouter API key is correct
   - Check your internet connection

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check [issues page](https://github.com/yourusername/prescription-parser/issues).

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [OpenRouter](https://openrouter.ai/) for LLM API access
- [pdf2image](https://github.com/Belval/pdf2image) for PDF conversion
- [Pillow](https://python-pillow.org/) for image processing

---
