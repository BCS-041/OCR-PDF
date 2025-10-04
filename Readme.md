psm --> In Tesseract OCR, PSM stands for Page Segmentation Mode. This parameter dictates how Tesseract analyzes an input image to identify and segment text regions before performing optical character recognition. Choosing the correct PSM is crucial for achieving accurate OCR results, as different modes are optimized for various text layouts and image characteristics.

Common PSM modes and their uses:
Tesseract offers several PSM modes, each suited for different scenarios:
$ tesseract --help-psm
Page segmentation modes:
  0    Orientation and script detection (OSD) only.
  1    Automatic page segmentation with OSD.
  2    Automatic page segmentation, but no OSD, or OCR. (not implemented)
  3    Fully automatic page segmentation, but no OSD. (Default)
  4    Assume a single column of text of variable sizes.
  5    Assume a single uniform block of vertically aligned text.
  6    Assume a single uniform block of text.
  7    Treat the image as a single text line.
  8    Treat the image as a single word.
  9    Treat the image as a single word in a circle.
 10    Treat the image as a single character.
 11    Sparse text. Find as much text as possible in no particular order.
 12    Sparse text with OSD.
 13    Raw line. Treat the image as a single text line,bypassing hacks that are Tesseract-specific.


For more : https://pyimagesearch.com/2021/11/15/tesseract-page-segmentation-modes-psms-explained-how-to-improve-your-ocr-accuracy/



"""
Prescription extraction pipeline (rewritten)

Features:
- OCR via pytesseract (per-word confidences)
- Sends OCR text + images to OpenRouter (LLM) for structured extraction
- LLM asked to return numeric self-confidence (0-100) per field
- Post-process hybrid confidence (OCR + LLM) with conflict detection
- Produces Manual_QA_Flags and a clear Confidence_Level with reasons
- Works with remote URLs (images/pdf) and local images/pdf in IMAGES_FOLDER
"""

