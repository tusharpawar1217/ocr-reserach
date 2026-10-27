"""
Engine-agnostic line clustering for OCR output.

Fixes fragmentation where single words land on their own line because
Tesseract's internal line_num (or EasyOCR/PaddleOCR's per-detection grouping)
drifts on tilted/curved/skewed photos of boards.

Core idea: ignore whatever "line number" the engine assigns. Instead, take
every word's bounding box, cluster boxes by vertical center position
(y_center), then sort each cluster left-to-right by x. This is purely
geometric, so it works the same way regardless of which OCR engine produced
the boxes -- Tesseract, EasyOCR, and PaddleOCR all get normalized into the
same (text, left, top, width, height) shape before clustering.
"""

from dataclasses import dataclass
from typing import List
import numpy as np
import pytesseract
from pytesseract import Output

@dataclass
class WordBox:
    text: str
    left: float
    top: float
    width: float
    height: float

    @property
    def y_center(self) -> float:
        return self.top + self.height / 2

    @property
    def x_left(self) -> float:
        return self.left

def cluster_words_into_lines(words: List[WordBox], y_tolerance_ratio: float = 0.6) -> List[str]:
    """
    Group word boxes into visual lines by y_center proximity, then sort each
    line left-to-right by x.
    
    y_tolerance_ratio: how close two words' y_centers must be (relative to
    average word height) to count as "same line". 0.5-0.7 works well for
    photographed boards; lower it if two real distinct lines are getting
    merged, raise it if one real line is still splitting into two.
    """
    if not words:
        return []
    
    # sort by vertical position first
    words = sorted(words, key=lambda w: w.y_center)
    
    lines: List[List[WordBox]] = []
    current_line: List[WordBox] = [words[0]]
    current_y = words[0].y_center
    current_h = words[0].height
    
    for w in words[1:]:
        tolerance = current_h * y_tolerance_ratio
        if abs(w.y_center - current_y) <= tolerance:
            current_line.append(w)
            # update running average so tolerance adapts as we go down the line
            current_y = np.mean([x.y_center for x in current_line])
            current_h = np.mean([x.height for x in current_line])
        else:
            lines.append(current_line)
            current_line = [w]
            current_y = w.y_center
            current_h = w.height
    
    lines.append(current_line)
    
    # left-to-right order within each line, then join into text
    joined_lines = []
    for line in lines:
        line_sorted = sorted(line, key=lambda w: w.x_left)
        joined_lines.append(" ".join(w.text for w in line_sorted if w.text.strip()))
    
    return [ln for ln in joined_lines if ln.strip()]

# ---------------------------------------------------------------------------
# Per-engine adapters: convert each engine's native output into WordBox list
# ---------------------------------------------------------------------------

def words_from_tesseract(image, lang: str = "hin") -> List[WordBox]:
    data = pytesseract.image_to_data(image, lang=lang, output_type=Output.DICT)
    words = []
    for i in range(len(data["text"])):
        text = data["text"][i]
        if not text.strip():
            continue
        words.append(WordBox(
            text=text,
            left=data["left"][i],
            top=data["top"][i],
            width=data["width"][i],
            height=data["height"][i],
        ))
    return words

def words_from_easyocr(results) -> List[WordBox]:
    """
    results = reader.readtext(image) -> list of (bbox, text, conf)
    bbox = [[x1,y1],[x2,y1],[x2,y2],[x1,y2]] (4 corner points)
    """
    words = []
    for bbox, text, conf in results:
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        words.append(WordBox(
            text=text,
            left=min(xs),
            top=min(ys),
            width=max(xs) - min(xs),
            height=max(ys) - min(ys),
        ))
    return words

def words_from_paddleocr(results) -> List[WordBox]:
    """
    results = paddle_ocr_result[0] -> list of [box, (text, conf)]
    """
    words = []
    for box, (text, conf) in results:
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        words.append(WordBox(
            text=text,
            left=min(xs),
            top=min(ys),
            width=max(xs) - min(xs),
            height=max(ys) - min(ys),
        ))
    return words

# ---------------------------------------------------------------------------
# Drop-in replacement extraction functions
# ---------------------------------------------------------------------------

def extract_text_tesseract(image, lang: str = "hin") -> str:
    words = words_from_tesseract(image, lang=lang)
    lines = cluster_words_into_lines(words)
    return "\n".join(lines)

def extract_text_easyocr(reader, image) -> str:
    results = reader.readtext(image)
    words = words_from_easyocr(results)
    lines = cluster_words_into_lines(words)
    return "\n".join(lines)

def extract_text_paddleocr(paddle_ocr, image) -> str:
    result = paddle_ocr.ocr(image)
    words = words_from_paddleocr(result[0])
    lines = cluster_words_into_lines(words)
    return "\n".join(lines)
