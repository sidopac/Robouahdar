"""
وحدة سياق المحادثة - إدارة وتخزين سياق المحادثات مع المستخدمين
"""
import json
import time
from collections import defaultdict
import os
import re
from firebase_db import save_conversation_session

# تخزين سياق المحادثة لكل مستخدم
# user_id -> list of [timestamp, sender, message, metadata]
user_conversations = defaultdict(list)

# تخزين المعلومات المستخرجة من المحادثات
# user_id -> dict of extracted information
user_context = defaultdict(dict)

def add_message(user_id, message, sender='user', metadata=None):
    """
    إضافة رسالة إلى سياق المحادثة
    
    Args:
        user_id (str): معرف المستخدم
        message (str): الرسالة
        sender (str): المرسل ('user' أو 'bot')
        metadata (dict): بيانات إضافية عن الرسالة
    """
    if metadata is None:
        metadata = {}
    
    user_conversations[user_id].append({
        'timestamp': time.time(),
        'sender': sender,
        'message': message,
        'metadata': metadata
    })
    
    # تحليل الرسالة واستخراج المعلومات إذا كانت من المستخدم
    if sender == 'user':
        extract_context(user_id, message)
    
    # حفظ الجلسة في Firebase إذا كانت هناك أكثر من رسالتين
    if len(user_conversations[user_id]) >= 2:
        try:
            save_conversation_session(user_id, user_conversations[user_id], user_context[user_id])
        except Exception as e:
            print(f"خطأ في حفظ جلسة المحادثة: {str(e)}")

def get_conversation_history(user_id, limit=10):
    """
    الحصول على تاريخ المحادثة للمستخدم
    
    Args:
        user_id (str): معرف المستخدم
        limit (int): الحد الأقصى لعدد الرسائل
        
    Returns:
        list: قائمة الرسائل الأخيرة
    """
    conversation = user_conversations.get(user_id, [])
    return conversation[-limit:] if conversation else []

def get_last_message(user_id, sender=None):
    """
    الحصول على آخر رسالة في سياق المحادثة
    
    Args:
        user_id (str): معرف المستخدم
        sender (str): المرسل ('user' أو 'bot' أو None للكل)
        
    Returns:
        dict: آخر رسالة
    """
    conversation = user_conversations.get(user_id, [])
    
    if not conversation:
        return None
    
    if sender:
        # البحث عن آخر رسالة من المرسل المحدد
        for msg in reversed(conversation):
            if msg['sender'] == sender:
                return msg
        return None
    
    # إرجاع آخر رسالة بغض النظر عن المرسل
    return conversation[-1]

def extract_context(user_id, message):
    """
    استخراج معلومات السياق من رسالة المستخدم
    
    Args:
        user_id (str): معرف المستخدم
        message (str): رسالة المستخدم
    """
    context = user_context[user_id]
    
    # البحث عن أسئلة عن الأسعار
    price_patterns = [
        r'كم سعر[^؟]+',
        r'ما هو سعر[^؟]+',
        r'بكم[^؟]+',
        r'السعر[^؟]+'
    ]
    
    for pattern in price_patterns:
        if re.search(pattern, message):
            context['last_topic'] = 'سعر'
            # محاولة استخراج اسم المنتج
            product_match = re.search(r'سعر\s+(\w+)', message)
            if product_match:
                context['product'] = product_match.group(1)
            break
    
    # البحث عن أسئلة عن المكان أو التوصيل
    location_patterns = [
        r'وين[^؟]+',
        r'أين[^؟]+',
        r'فين[^؟]+',
        r'مكان[^؟]+',
        r'العنوان[^؟]+',
        r'التوصيل[^؟]+',
        r'التسليم[^؟]+'
    ]
    
    for pattern in location_patterns:
        if re.search(pattern, message):
            # إذا كان السؤال السابق عن السعر، فهذا سؤال مرتبط
            if context.get('last_topic') == 'سعر':
                context['last_topic'] = 'توصيل'
                context['related_to_previous'] = True
            else:
                context['last_topic'] = 'مكان'
                context['related_to_previous'] = False
            break

def get_context(user_id):
    """
    الحصول على سياق المحادثة للمستخدم
    
    Args:
        user_id (str): معرف المستخدم
        
    Returns:
        dict: سياق المحادثة
    """
    return user_context.get(user_id, {})

def clear_context(user_id):
    """
    مسح سياق المحادثة للمستخدم
    
    Args:
        user_id (str): معرف المستخدم
    """
    if user_id in user_context:
        del user_context[user_id]
    
    if user_id in user_conversations:
        del user_conversations[user_id]

def save_all_contexts():
    """
    حفظ جميع سياقات المحادثات في ملف
    """
    data = {
        'conversations': dict(user_conversations),
        'contexts': dict(user_context)
    }
    
    try:
        with open('conversation_contexts.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"خطأ في حفظ سياقات المحادثات: {str(e)}")

def load_all_contexts():
    """
    تحميل جميع سياقات المحادثات من ملف
    """
    if not os.path.exists('conversation_contexts.json'):
        return
    
    try:
        with open('conversation_contexts.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # تحويل القواميس إلى defaultdict
            for user_id, conversation in data.get('conversations', {}).items():
                user_conversations[user_id] = conversation
            
            for user_id, context in data.get('contexts', {}).items():
                user_context[user_id] = context
    except Exception as e:
        print(f"خطأ في تحميل سياقات المحادثات: {str(e)}")

# تحميل السياقات عند بدء تشغيل الوحدة
load_all_contexts()