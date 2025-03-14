"""
Natural Language Processing Module for Arabic Chatbot
"""
import nltk
import os
import re
import string
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import arabic_reshaper
from bidi.algorithm import get_display

# إنشاء دليل لتخزين بيانات NLTK
nltk_data_path = os.path.join(os.getcwd(), 'nltk_data')
if not os.path.exists(nltk_data_path):
    os.makedirs(nltk_data_path)
nltk.data.path.append(nltk_data_path)

print("تحميل موارد معالجة اللغة الطبيعية...")

# تحميل البيانات اللازمة لمعالجة اللغة العربية
try:
    # تنزيل البيانات المطلوبة
    nltk.download('punkt', download_dir=nltk_data_path)
    nltk.download('stopwords', download_dir=nltk_data_path)
    print("تم تحميل موارد NLTK بنجاح!")
except Exception as e:
    print(f"حدث خطأ أثناء تحميل موارد NLTK: {str(e)}")
    
# تعريف كلمات التوقف العربية محليًا في حالة فشل تحميل NLTK
ARABIC_STOPWORDS = set([
    'من', 'إلى', 'عن', 'على', 'في', 'هو', 'هي', 'هم', 'انت', 'انتم', 'انتما',
    'هما', 'ذلك', 'التي', 'الذي', 'ما', 'كيف', 'اين', 'متى', 'لماذا', 'هل',
    'نعم', 'لا', 'ليس', 'مع', 'عند', 'عندما', 'او', 'و', 'ثم', 'لكن', 'حتى',
    'اذا', 'ان', 'بعد', 'قبل', 'كل', 'بعض', 'غير', 'لم', 'لن', 'الى', 'الا'
])

def preprocess_arabic_text(text):
    """
    معالجة النص العربي
    
    Args:
        text (str): النص المدخل
        
    Returns:
        str: النص بعد المعالجة
    """
    if not text:
        return ""
        
    try:
        # تنظيف النص - إبقاء الحروف العربية والمسافات فقط
        text = re.sub(r'[^\u0600-\u06FF\s]', ' ', text)
        
        # محاولة تحويل النص إلى شكل موحد باستخدام arabic_reshaper
        try:
            text = arabic_reshaper.reshape(text)
            text = get_display(text)
        except Exception as e:
            print(f"تخطي إعادة تشكيل النص العربي بسبب: {str(e)}")
        
        # إزالة المسافات المتعددة وتنظيف النص
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    except Exception as e:
        print(f"خطأ في معالجة النص: {str(e)}")
        # إرجاع النص الأصلي في حالة حدوث خطأ
        return text.strip() if text else ""

def tokenize_arabic(text):
    """
    تقسيم النص العربي إلى كلمات
    
    Args:
        text (str): النص المدخل
        
    Returns:
        list: قائمة الكلمات
    """
    try:
        return word_tokenize(text)
    except Exception as e:
        print(f"استخدام تقسيم الكلمات البسيط بسبب: {str(e)}")
        # استخدام طريقة بسيطة لتقسيم النص إلى كلمات
        # إزالة علامات الترقيم ثم تقسيم النص بناءً على المسافات
        text = text.translate(str.maketrans('', '', string.punctuation))
        return text.split()

def remove_arabic_stopwords(tokens):
    """
    إزالة الكلمات الشائعة من النص العربي
    
    Args:
        tokens (list): قائمة الكلمات
        
    Returns:
        list: قائمة الكلمات بدون الكلمات الشائعة
    """
    # محاولة استخدام stopwords من NLTK، وإلا استخدام القائمة المحلية
    try:
        stop_words = set(stopwords.words('arabic'))
    except Exception as e:
        print(f"استخدام قائمة الكلمات المحلية بسبب: {str(e)}")
        stop_words = ARABIC_STOPWORDS
    
    return [token for token in tokens if token not in stop_words]

def calculate_similarity(text1, text2):
    """
    حساب مدى التشابه بين نصين
    
    Args:
        text1 (str): النص الأول
        text2 (str): النص الثاني
        
    Returns:
        float: درجة التشابه (0-1)
    """
    # معالجة النصوص
    text1 = preprocess_arabic_text(text1)
    text2 = preprocess_arabic_text(text2)
    
    # تقسيم النصوص إلى كلمات
    tokens1 = set(remove_arabic_stopwords(tokenize_arabic(text1)))
    tokens2 = set(remove_arabic_stopwords(tokenize_arabic(text2)))
    
    # حساب التشابه باستخدام معامل جاكارد
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    
    if union == 0:
        return 0
    
    return intersection / union