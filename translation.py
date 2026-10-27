"""
Translation functions with 100% open-source backends
All components are fully open-source and free:
- Deep Translator: Open-source client for Google Translate API
- Argos Translate: Fully offline neural translation
- MyMemory API: Free translation API
- Offline Dictionary: Local word-by-word translation
"""

from typing import Optional, Dict
import streamlit as st
import requests
import json
import urllib.parse
import time

# Try importing different translation libraries (ALL OPEN SOURCE)
TRANSLATION_AVAILABLE = False
BACKEND_INFO = []

try:
    from deep_translator import GoogleTranslator, MyMemoryTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
    TRANSLATION_AVAILABLE = True  
    BACKEND_INFO.append("Deep Translator (100% Open Source)")
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False

try:
    import argostranslate.package
    import argostranslate.translate
    ARGOS_AVAILABLE = True
    TRANSLATION_AVAILABLE = True
    BACKEND_INFO.append("Argos Translate (Offline Neural Translation - 100% Open Source)")
except ImportError:
    ARGOS_AVAILABLE = False

# Always have offline fallback
TRANSLATION_AVAILABLE = True
BACKEND_INFO.append("Offline Dictionary (Always Available)")

# Comprehensive language mappings for all major Indian languages
LANGUAGE_MAPPING = {
    "English": "en",
    "Hindi": "hi", 
    "Marathi": "mr",
    "Bengali": "bn",
    "Gujarati": "gu",
    "Tamil": "ta",
    "Telugu": "te",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Oriya/Odia": "or",
    "Punjabi": "pa",
    "Assamese": "as",
    "Nepali": "ne",
    "Urdu": "ur",
    "Sanskrit": "sa",
    "Sindhi": "sd"
}

REVERSE_LANGUAGE_MAPPING = {v: k for k, v in LANGUAGE_MAPPING.items()}

def get_available_languages():
    """Get list of available target languages"""
    return list(LANGUAGE_MAPPING.keys())

def get_language_code(language_name: str) -> str:
    """Get language code from language name"""
    return LANGUAGE_MAPPING.get(language_name, "en")

def get_language_name(language_code: str) -> str:
    """Get language name from language code"""
    return REVERSE_LANGUAGE_MAPPING.get(language_code, "English")

def translate_with_argos(text: str, target_code: str, source_code: str = "en") -> Dict:
    """Fully offline neural translation using Argos Translate (100% Open Source)"""
    try:
        if not ARGOS_AVAILABLE:
            raise ImportError("argostranslate not available")
        
        # Check if language packages are installed
        installed_languages = argostranslate.translate.get_installed_languages()
        
        # Try to find matching language packages
        from_lang = None
        to_lang = None
        
        for lang in installed_languages:
            if lang.code == source_code:
                from_lang = lang
            if lang.code == target_code:
                to_lang = lang
        
        if not from_lang or not to_lang:
            return {
                "success": False,
                "error": f"Language packages not installed for {source_code}→{target_code}. Install via Argos Translate.",
                "backend": "Argos Translate",
                "note": "Argos requires language pack downloads"
            }
        
        # Get translation
        translation = from_lang.get_translation(to_lang)
        if translation:
            translated_text = translation.translate(text)
            return {
                "success": True,
                "translated_text": translated_text,
                "backend": "Argos Translate (Offline Neural)",
                "note": "100% offline translation"
            }
        else:
            return {
                "success": False,
                "error": f"No translation path available for {source_code}→{target_code}",
                "backend": "Argos Translate"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Argos Translate failed: {str(e)}",
            "backend": "Argos Translate"
        }

def translate_with_mymemory(text: str, target_code: str, source_code: str = "auto") -> Dict:
    """MyMemory Free Translation API (Open Source API)"""
    try:
        # MyMemory requires specific locale codes (e.g., en-GB not just en)
        # Map simple codes to locale codes
        locale_map = {
            "en": "en-GB",
            "hi": "hi-IN",
            "mr": "mr-IN",
            "bn": "bn-IN",
            "gu": "gu-IN",
            "ta": "ta-IN",
            "te": "te-IN",
            "kn": "kn-IN",
            "ml": "ml-IN",
            "or": "or-IN",
            "pa": "pa-IN",
            "as": "as-IN",
            "ne": "ne-NP",
            "ur": "ur-PK",
            "sa": "sa-IN",
            "sd": "sd-PK"
        }
        
        target_locale = locale_map.get(target_code, target_code)
        source_locale = locale_map.get(source_code, source_code) if source_code != "auto" else "en-GB"
        
        # Use Deep Translator's MyMemory wrapper
        if DEEP_TRANSLATOR_AVAILABLE:
            translator = MyMemoryTranslator(source=source_locale, target=target_locale)
            translated = translator.translate(text)
            
            if translated and translated.strip():
                return {
                    "success": True,
                    "translated_text": translated,
                    "backend": "MyMemory API (Open Source)"
                }
        
        # Fallback to direct API call
        encoded_text = urllib.parse.quote(text[:500])  # Limit to 500 chars
        url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair={source_locale}|{target_locale}"
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'responseData' in data and data['responseData']['translatedText']:
                return {
                    "success": True,
                    "translated_text": data['responseData']['translatedText'],
                    "backend": "MyMemory Free API (Open Source)"
                }
    except Exception as e:
        return {
            "success": False,
            "error": f"MyMemory API failed: {str(e)}",
            "backend": "MyMemory API"
        }
    
    return {
        "success": False,
        "error": "MyMemory API translation failed",
        "backend": "MyMemory API"
    }

def translate_with_offline_dictionary(text: str, target_language: str) -> Dict:
    """Enhanced offline translation with better dictionaries"""
    
    # Comprehensive dictionaries for Indian languages
    dictionaries = {
        "en": {  # English (for testing/fallback)
            # Common OCR words
            "सरकार": "government", "गाँव": "village", "जिला": "district", "राज्य": "state",
            "योजना": "scheme", "कार्य": "work", "रोजगार": "employment", "परियोजना": "project",
            "नाम": "name", "तारीख": "date", "राशि": "amount", "कुल": "total",
            "गाव": "village", "रक्कम": "amount", "दिनांक": "date", "एकूण": "total",
        },
        "hi": {  # Hindi
            # Government/Official terms
            "government": "सरकार", "village": "गाँव", "district": "जिला", "state": "राज्य",
            "scheme": "योजना", "work": "कार्य", "employment": "रोजगार", "project": "परियोजना",
            "development": "विकास", "rural": "ग्रामीण", "urban": "शहरी", "national": "राष्ट्रीय",
            "ministry": "मंत्रालय", "department": "विभाग", "office": "कार्यालय", "officer": "अधिकारी",
            
            # MGNREGA specific terms
            "mgnrega": "मनरेगा", "mahatma": "महात्मा", "gandhi": "गांधी", "guarantee": "गारंटी",
            "act": "अधिनियम", "wages": "मजदूरी", "days": "दिन", "card": "कार्ड",
            
            # Common words
            "name": "नाम", "date": "तारीख", "amount": "राशि", "total": "कुल", "number": "संख्या",
            "address": "पता", "phone": "फोन", "mobile": "मोबाइल", "email": "ईमेल",
            
            # Greetings
            "hello": "नमस्ते", "thank you": "धन्यवाद", "good morning": "सुप्रभात"
        },
        "mr": {  # Marathi
            # Government/Official terms  
            "government": "सरकार", "village": "गाव", "district": "जिल्हा", "state": "राज्य",
            "scheme": "योजना", "work": "काम", "employment": "रोजगार", "project": "प्रकल्प",
            "development": "विकास", "rural": "ग्रामीण", "urban": "शहरी", "national": "राष्ट्रीय",
            "ministry": "मंत्रालय", "department": "विभाग", "office": "कार्यालय", "officer": "अधिकारी",
            
            # MGNREGA terms
            "mgnrega": "मनरेगा", "mahatma": "महात्मा", "gandhi": "गांधी", "guarantee": "हमी",
            "act": "अधिनियम", "wages": "मजुरी", "days": "दिवस", "card": "कार्ड",
            
            # Common words
            "name": "नाव", "date": "दिनांक", "amount": "रक्कम", "total": "एकूण", "number": "क्रमांक",
            "address": "पत्ता", "phone": "फोन", "mobile": "मोबाईल", "email": "ईमेल",
            
            # Greetings
            "hello": "नमस्कार", "thank you": "धन्यवाद", "good morning": "सुप्रभात"
        },
        "bn": {  # Bengali
            "government": "সরকার", "village": "গ্রাম", "district": "জেলা", "state": "রাজ্য",
            "scheme": "প্রকল্প", "work": "কাজ", "employment": "কর্মসংস্থান", 
            "hello": "নমস্কার", "thank you": "ধন্যবাদ"
        },
        "gu": {  # Gujarati
            "government": "સરકાર", "village": "ગામ", "district": "જિલ્લો", "state": "રાજ્ય",
            "scheme": "યોજના", "work": "કામ", "employment": "રોજગાર",
            "hello": "નમસ્તે", "thank you": "આભાર"
        },
        "ta": {  # Tamil
            "government": "அரசு", "village": "கிராமம்", "district": "மாவட்டம்", "state": "மாநிலம்",
            "scheme": "திட்டம்", "work": "வேலை", "employment": "வேலைவாய்ப்பு",
            "hello": "வணக்கம்", "thank you": "நன்றி"
        }
    }
    
    target_code = get_language_code(target_language)
    word_dict = dictionaries.get(target_code, {})
    
    if not word_dict:
        return {
            "success": False,
            "error": f"No offline dictionary for {target_language}",
            "backend": "Offline Dictionary"
        }
    
    # Smart translation logic
    original_text = text.lower().strip()
    translated_parts = []
    words = original_text.split()
    
    translations_made = 0
    for word in words:
        # Remove punctuation for matching
        clean_word = word.strip('.,!?;:()[]{}')
        if clean_word in word_dict:
            translated_parts.append(word_dict[clean_word])
            translations_made += 1
        else:
            # Keep original word
            translated_parts.append(word)
    
    if translations_made > 0:
        result_text = " ".join(translated_parts)
        return {
            "success": True,
            "translated_text": result_text,
            "backend": "Offline Dictionary",
            "translations_count": translations_made,
            "note": f"Translated {translations_made} words using offline dictionary"
        }
    else:
        return {
            "success": False,
            "error": "No matching words found in offline dictionary",
            "backend": "Offline Dictionary"
        }

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes, no spinner
def translate_text(text: str, target_language: str, source_language: str = "auto") -> Dict:
    """
    Multi-backend translation using ONLY 100% open-source solutions
    Translation backends (in priority order):
    1. Offline Dictionary (Fast, always works for common words)
    2. Deep Translator (Open-source client for Google Translate API) - DISABLED on Streamlit Cloud
    3. Argos Translate (Offline neural translation - 100% open source)
    4. MyMemory API (Free open-source translation API - skipped for unsupported languages)
    """
    if not text or not text.strip():
        return {
            "success": False,
            "error": "No text provided for translation",
            "original_text": text,
            "translated_text": "",
            "source_language": source_language,
            "target_language": target_language
        }
    
    target_code = get_language_code(target_language)
    source_code = get_language_code(source_language) if source_language != "auto" else "auto"
    backends_tried = []
    
    # Detect if running on Streamlit Cloud (rate limits are harsh there)
    import os
    is_cloud = os.getenv("STREAMLIT_SHARING_MODE") or os.getenv("STREAMLIT_CLOUD")
    
    # Backend 1 (FIRST): Try Offline Dictionary (Fast, no rate limits!)
    offline_result = translate_with_offline_dictionary(text, target_language)
    if offline_result["success"]:
        # Check if we got a reasonable translation (not just original text)
        if offline_result["translated_text"].strip() != text.strip():
            return {
                "success": True,
                "error": None,
                "original_text": text,
                "translated_text": offline_result["translated_text"],
                "source_language": source_language,
                "target_language": target_language,
                "target_language_code": target_code,
                "backend": "Offline Dictionary (100% Open Source)",
                "note": offline_result.get("note", "Local dictionary translation")
            }
    backends_tried.append(offline_result["error"])
    
    # Backend 2: Skip Deep Translator on cloud (rate limited), use on local only
    if DEEP_TRANSLATOR_AVAILABLE and not is_cloud:
        try:
            # Add delay to avoid rate limiting (Google allows ~5 requests/second)
            time.sleep(0.3)  # 300ms delay
            
            translator = GoogleTranslator(source=source_code, target=target_code)
            translated = translator.translate(text[:1000])  # Limit text length
            
            if translated and translated.strip() != text.strip():
                return {
                    "success": True,
                    "error": None,
                    "original_text": text,
                    "translated_text": translated,
                    "source_language": source_language,
                    "target_language": target_language,
                    "target_language_code": target_code,
                    "backend": "Deep Translator (Open Source)",
                    "note": "Using free Google Translate API via open-source client"
                }
            else:
                backends_tried.append("Deep-Translator returned same text (may be already in target language)")
        except Exception as e:
            error_msg = str(e)
            if "too many requests" in error_msg.lower():
                backends_tried.append("Deep-Translator: Rate limit exceeded. Try again in a few seconds.")
            else:
                backends_tried.append(f"Deep-Translator: {error_msg}")
    elif is_cloud:
        backends_tried.append("Deep-Translator: Disabled on Streamlit Cloud due to rate limits")
    
    # Backend 3: Try Argos Translate (100% offline, neural translation)
    if ARGOS_AVAILABLE and source_code != "auto":
        result = translate_with_argos(text, target_code, source_code)
        if result["success"]:
            return {
                "success": True,
                "error": None,
                "original_text": text,
                "translated_text": result["translated_text"],
                "source_language": source_language,
                "target_language": target_language,
                "target_language_code": target_code,
                "backend": "Argos Translate (Offline Neural - 100% Open Source)",
                "note": result.get("note", "Fully offline translation")
            }
        backends_tried.append(result["error"])
    
    # Backend 4: Try MyMemory API (Skip Marathi as it's not supported)
    if target_code != "mr":  # MyMemory doesn't support Marathi
        mymemory_result = translate_with_mymemory(text, target_code, source_code)
        if mymemory_result["success"]:
            return {
                "success": True,
                "error": None,
                "original_text": text,
                "translated_text": mymemory_result["translated_text"],
                "source_language": source_language,
                "target_language": target_language,
                "target_language_code": target_code,
                "backend": "MyMemory API (Open Source)",
                "note": "Free translation API"
            }
        else:
            backends_tried.append(mymemory_result["error"])
    else:
        backends_tried.append("MyMemory API: Marathi (mr) not supported by this service")
    
    # All failed - return with helpful message
    if offline_result.get("translated_text"):
        # If offline dictionary had partial translation, return it with warning
        return {
            "success": True,
            "error": "Online services failed, using offline dictionary (partial translation)",
            "original_text": text,
            "translated_text": offline_result["translated_text"],
            "source_language": source_language,
            "target_language": target_language,
            "target_language_code": target_code,
            "backend": "Offline Dictionary (Fallback)",
            "note": f"Online services unavailable. {offline_result.get('note', '')}",
            "warning": "This is a partial translation. Some words may not be translated."
        }
    
    # If translating TO English from Indian language, return original as fallback
    if target_code == "en":
        return {
            "success": True,
            "error": "Translation services unavailable",
            "original_text": text,
            "translated_text": text,  # Return original text
            "source_language": source_language,
            "target_language": target_language,
            "backends_tried": backends_tried,
            "note": "Translation to English unavailable. Showing original text.",
            "warning": "Translation services are currently rate-limited. Original text shown."
        }
    
    return {
        "success": False,
        "error": f"All translation methods failed. Backends tried: {'; '.join(backends_tried)}",
        "original_text": text,
        "translated_text": text,  # Return original text as fallback
        "source_language": source_language,
        "target_language": target_language,
        "backends_tried": backends_tried,
        "suggestion": "Translation services rate-limited on Streamlit Cloud. Wait 60 seconds or use shorter text. Showing original text for now."
    }

def get_translation_backends():
    """Get information about available translation backends (ALL OPEN SOURCE)"""
    return {
        "available_backends": BACKEND_INFO,
        "deep_translator_available": DEEP_TRANSLATOR_AVAILABLE,
        "argos_translate_available": ARGOS_AVAILABLE,
        "offline_available": True,
        "total_languages": len(LANGUAGE_MAPPING),
        "note": "All translation backends are 100% open source"
    }

def batch_translate(texts: list, target_language: str, source_language: str = "auto") -> list:
    """
    Translate multiple texts
    
    Args:
        texts: List of texts to translate
        target_language: Target language name or code
        source_language: Source language code (default: "auto")
    
    Returns:
        List of translation result dictionaries
    """
    results = []
    
    for text in texts:
        result = translate_text(text, target_language, source_language)
        results.append(result)
    
    return results

def is_translation_needed(text: str, target_language: str) -> bool:
    """
    Simple heuristic to check if translation might be needed
    
    Args:
        text: Text to check
        target_language: Target language
    
    Returns:
        True if translation might be needed, False otherwise
    """
    if not text or not text.strip():
        return False
    
    target_code = get_language_code(target_language)
    
    # Simple heuristics based on script
    if target_code == "hi":  # Hindi
        # Check if text contains Devanagari script
        devanagari_range = any('\u0900' <= char <= '\u097F' for char in text)
        return not devanagari_range
    
    elif target_code == "mr":  # Marathi (also uses Devanagari)
        devanagari_range = any('\u0900' <= char <= '\u097F' for char in text)
        return not devanagari_range
    
    elif target_code == "bn":  # Bengali
        # Check if text contains Bengali script
        bengali_range = any('\u0980' <= char <= '\u09FF' for char in text)
        return not bengali_range
    
    elif target_code == "en":  # English
        # Check if text contains mostly ASCII
        ascii_chars = sum(1 for char in text if ord(char) < 128)
        return ascii_chars / len(text) < 0.7  # Less than 70% ASCII
    
    # Default: assume translation might be needed
    return True

def get_translation_confidence(result: Dict) -> str:
    """
    Get a simple confidence assessment for translation
    
    Args:
        result: Translation result dictionary
    
    Returns:
        Confidence level as string
    """
    if not result.get("success", False):
        return "Failed"
    
    original = result.get("original_text", "")
    translated = result.get("translated_text", "")
    
    if not original or not translated:
        return "No translation"
    
    if len(translated) < len(original) * 0.3:
        return "Low confidence (translation too short)"
    
    if len(translated) > len(original) * 3:
        return "Low confidence (translation too long)"
    
    if original.strip() == translated.strip():
        return "No change (same text)"
    
    return "Good"

if __name__ == "__main__":
    # Test translation functions
    print("Testing translation functions...")
    
    if not DEEP_TRANSLATOR_AVAILABLE:
        print("❌ deep-translator not available")
        exit(1)
    
    print("✅ deep-translator available")
    
    # Test languages
    languages = get_available_languages()
    print(f"Available languages: {languages}")
    
    # Test translation
    test_text = "Hello, this is a test message."
    
    for lang in ["Hindi", "Marathi"]:
        print(f"\nTesting translation to {lang}...")
        result = translate_text(test_text, lang)
        
        if result["success"]:
            print(f"✅ Original: {result['original_text']}")
            print(f"✅ Translated: {result['translated_text']}")
            print(f"   Confidence: {get_translation_confidence(result)}")
        else:
            print(f"❌ Translation failed: {result['error']}")
    
    print("\n✅ Translation tests completed!")


def translate_text_no_cache(text: str, target_language: str, source_language: str = "auto") -> Dict:
    """
    Translation without caching - allows multiple translations to different languages
    Uses ONLY 100% open-source backends (same as translate_text but without cache)
    """
    if not text or not text.strip():
        return {
            "success": False,
            "error": "No text provided for translation",
            "original_text": text,
            "translated_text": "",
            "source_language": source_language,
            "target_language": target_language
        }
    
    target_code = get_language_code(target_language)
    source_code = get_language_code(source_language) if source_language != "auto" else "auto"
    backends_tried = []
    
    # Backend 1: Try Deep Translator (Open-source)
    if DEEP_TRANSLATOR_AVAILABLE:
        try:
            translator = GoogleTranslator(source=source_code, target=target_code)
            translated = translator.translate(text)
            
            if translated and translated.strip() != text.strip():
                return {
                    "success": True,
                    "error": None,
                    "original_text": text,
                    "translated_text": translated,
                    "source_language": source_language,
                    "target_language": target_language,
                    "target_language_code": target_code,
                    "backend": "Deep Translator (Open Source)"
                }
            else:
                backends_tried.append("Deep-Translator returned same text")
        except Exception as e:
            backends_tried.append(f"Deep-Translator: {str(e)}")
    
    # Backend 2: Try Argos Translate (100% offline)
    if ARGOS_AVAILABLE and source_code != "auto":
        result = translate_with_argos(text, target_code, source_code)
        if result["success"]:
            return {
                "success": True,
                "error": None,
                "original_text": text,
                "translated_text": result["translated_text"],
                "source_language": source_language,
                "target_language": target_language,
                "target_language_code": target_code,
                "backend": "Argos Translate (Offline - 100% Open Source)"
            }
        backends_tried.append(result["error"])
    
    # Backend 3: Try MyMemory API
    mymemory_result = translate_with_mymemory(text, target_code, source_code)
    if mymemory_result["success"]:
        return {
            "success": True,
            "error": None,
            "original_text": text,
            "translated_text": mymemory_result["translated_text"],
            "source_language": source_language,
            "target_language": target_language,
            "target_language_code": target_code,
            "backend": "MyMemory API (Open Source)"
        }
    else:
        backends_tried.append(mymemory_result["error"])
    
    # Backend 4: Offline dictionary
    offline_result = translate_with_offline_dictionary(text, target_language)
    if offline_result["success"]:
        return {
            "success": True,
            "error": None,
            "original_text": text,
            "translated_text": offline_result["translated_text"],
            "source_language": source_language,
            "target_language": target_language,
            "target_language_code": target_code,
            "backend": "Offline Dictionary (100% Open Source)",
            "note": offline_result.get("note", "")
        }
    else:
        backends_tried.append(offline_result["error"])
    
    # All failed
    return {
        "success": False,
        "error": f"All translation methods failed. Backends tried: {'; '.join(backends_tried)}",
        "original_text": text,
        "translated_text": "",
        "source_language": source_language,
        "target_language": target_language,
        "backends_tried": backends_tried,
        "suggestion": "Check your internet connection or try with shorter text"
    }
