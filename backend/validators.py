"""
دوال للتحقق من صحة مفاتيح API
"""
import re
from typing import Dict, Any

def validate_gemini_key(key: str) -> Dict[str, Any]:
    """
    يتحقق من صحة مفتاح Gemini API
    """
    if not key:
        return {"valid": False, "error": "المفتاح فارغ"}
    
    # Gemini keys عادة تبدأ بـ AIzaSy وطولها 39 حرف، لكن قد تختلف
    # نتحقق فقط من أنه يبدأ بـ AIza ويكون طوله معقول
    if not key.startswith('AIza') or len(key) < 30:
        return {
            "valid": False, 
            "error": "مفتاح Gemini غير صحيح. يجب أن يبدأ بـ AIza"
        }
    
    return {"valid": True, "error": None}

def validate_kie_key(key: str) -> Dict[str, Any]:
    """
    يتحقق من صحة مفتاح Kie.ai API
    """
    if not key:
        return {"valid": False, "error": "المفتاح فارغ"}
    
    # Kie.ai keys عادة تبدأ بـ kie_ أو تكون طويلة
    if not (key.startswith('kie_') or len(key) >= 32):
        return {
            "valid": False,
            "error": "مفتاح Kie.ai غير صحيح. يجب أن يبدأ بـ kie_ أو يكون طوله 32 حرف على الأقل"
        }
    
    return {"valid": True, "error": None}

def validate_youtube_credentials(client_id: str, client_secret: str) -> Dict[str, Any]:
    """
    يتحقق من صحة بيانات YouTube OAuth
    """
    errors = []
    
    if not client_id:
        errors.append("Client ID مطلوب")
    elif not client_id.endswith('.apps.googleusercontent.com'):
        errors.append("Client ID يجب أن ينتهي بـ .apps.googleusercontent.com")
    
    if not client_secret:
        errors.append("Client Secret مطلوب")
    elif not client_secret.startswith('GOCSPX-'):
        errors.append("Client Secret يجب أن يبدأ بـ GOCSPX-")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def validate_sheet_id(sheet_id: str) -> Dict[str, Any]:
    """
    يتحقق من صحة Sheet ID
    """
    if not sheet_id:
        return {"valid": False, "error": "Sheet ID مطلوب"}
    
    if len(sheet_id) < 30:
        return {
            "valid": False,
            "error": "Sheet ID غير صحيح. يجب أن يكون طوله 30 حرف على الأقل"
        }
    
    return {"valid": True, "error": None}
