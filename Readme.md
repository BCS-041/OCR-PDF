# 📖 Tesseract OCR – Page Segmentation Mode (PSM)

In **Tesseract OCR**, **PSM** stands for *Page Segmentation Mode*.
This parameter dictates how Tesseract analyzes an input image to identify and segment text regions before performing optical character recognition.

Choosing the correct PSM is crucial for achieving accurate OCR results, as different modes are optimized for various text layouts and image characteristics.

### Common PSM Modes

Run the command to see available modes:

```bash
tesseract --help-psm
```

| Mode | Description                                                                          |
| ---- | ------------------------------------------------------------------------------------ |
| 0    | Orientation and script detection (OSD) only                                          |
| 1    | Automatic page segmentation with OSD                                                 |
| 2    | Automatic page segmentation, but no OSD, or OCR (not implemented)                    |
| 3    | Fully automatic page segmentation, but no OSD (Default)                              |
| 4    | Assume a single column of text of variable sizes                                     |
| 5    | Assume a single uniform block of vertically aligned text                             |
| 6    | Assume a single uniform block of text                                                |
| 7    | Treat the image as a single text line                                                |
| 8    | Treat the image as a single word                                                     |
| 9    | Treat the image as a single word in a circle                                         |
| 10   | Treat the image as a single character                                                |
| 11   | Sparse text, find as much text as possible in no particular order                    |
| 12   | Sparse text with OSD                                                                 |
| 13   | Raw line, treat the image as a single text line (bypassing Tesseract-specific hacks) |

🔗 **More details:** [Tesseract PSM Explained (PyImageSearch)](https://pyimagesearch.com/2021/11/15/tesseract-page-segmentation-modes-psms-explained-how-to-improve-your-ocr-accuracy/)

---

# 💊 Prescription Extraction Pipeline

### Features

* 🔍 **OCR via pytesseract** with per-word confidence scores
* 📡 **Sends OCR text + images to OpenRouter (LLM)** for structured extraction
* 📊 **LLM returns numeric self-confidence (0–100) per field**
* ⚖️ **Hybrid confidence calculation** (OCR + LLM) with conflict detection
* 🚩 **Manual QA flags** generated when inconsistencies are found
* ✅ Produces a clear **Confidence Level with reasons**
* 🌐 Works with both **remote URLs (images/PDFs)** and **local files in `IMAGES_FOLDER`**

---
