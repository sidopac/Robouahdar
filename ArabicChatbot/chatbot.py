"""
Arabic Learning Chatbot Module
Handles chat logic and response selection using NLP and Firebase
"""
import firebase_db
import nlp_processor
import random
import uuid
import conversation_context
import personalities
import bot_memory
import re
import time
import datetime

# مستوى التشابه المطلوب للاعتبار أن الرسالتين متشابهتين
SIMILARITY_THRESHOLD = 0.7

# تخزين إعدادات المستخدمين
user_settings = {}

# احتمالية تفعيل ميزات الذاكرة والشخصية
MEMORY_TRIGGER_CHANCE = 0.15  # 15% فرصة لتفعيل ميزة الذاكرة
MOOD_TRIGGER_CHANCE = 0.2    # 20% فرصة لذكر المزاج
DREAM_TRIGGER_CHANCE = 0.1   # 10% فرصة لذكر حلم
EMOTION_TRIGGER_CHANCE = 0.1 # 10% فرصة لذكر مشاعر

def get_response(message, user_id=None, personality_type=None):
    """
    الحصول على رد للرسالة المدخلة
    
    Args:
        message (str): رسالة المستخدم
        user_id (str): معرف المستخدم (اختياري)
        personality_type (str): نوع شخصية البوت (اختياري)
        
    Returns:
        str: رد البوت، أو None إذا لم يتم العثور على رد
    """
    # إنشاء معرف للمستخدم إذا لم يكن موجوداً
    if not user_id:
        user_id = str(uuid.uuid4())
    
    # التأكد من وجود إعدادات للمستخدم
    if user_id not in user_settings:
        user_settings[user_id] = {
            'personality': personality_type or 'مرح',
            'last_interaction': time.time(),
            'first_interaction': time.time(),
            'interaction_count': 0
        }
    
    # تسجيل التفاعل
    user_settings[user_id]['last_interaction'] = time.time()
    user_settings[user_id]['interaction_count'] = user_settings[user_id].get('interaction_count', 0) + 1
    
    # تحديث شخصية البوت إذا تم تحديدها
    if personality_type:
        user_settings[user_id]['personality'] = personality_type
    
    # الحصول على شخصية البوت الحالية
    current_personality = user_settings[user_id].get('personality', 'مرح')
    
    # إضافة الرسالة إلى سياق المحادثة وتسجيلها في ذاكرة البوت
    conversation_context.add_message(user_id, message, sender='user')
    bot_memory.record_conversation(user_id, message)
    
    # معالجة الرسالة
    normalized_message = nlp_processor.preprocess_arabic_text(message)
    
    # ---------------- التعامل مع الأوامر الخاصة ----------------
    
    # التعامل مع طلبات تغيير الشخصية
    if re.search(r'غير الشخصية|تغيير الشخصية|اجعل الشخصية|كن|تصرف', message, re.IGNORECASE):
        for personality in personalities.get_available_personalities():
            if personality in message:
                user_settings[user_id]['personality'] = personality
                response = f"تم تغيير شخصيتي إلى {personality}. " + personalities.get_greeting(personality)
                conversation_context.add_message(user_id, response, sender='bot')
                return response
    
    # التعامل مع أوامر الاستفسار عن الشخصيات المتاحة
    if re.search(r'ما هي الشخصيات|الشخصيات المتاحة|شخصيات البوت', message, re.IGNORECASE):
        available_personalities = personalities.get_available_personalities()
        response = "الشخصيات المتاحة هي: " + " | ".join(available_personalities)
        conversation_context.add_message(user_id, response, sender='bot')
        return response
    
    # التعامل مع طلبات المزاج
    if re.search(r'كيف حالك|كيف مزاجك|بماذا تشعر|كيف تشعر|عامل ايه', message, re.IGNORECASE):
        mood = bot_memory.get_current_mood()
        response = f"{mood['response_style']} {mood['emoji']}"
        response = personalities.format_response(response, current_personality)
        conversation_context.add_message(user_id, response, sender='bot')
        return response
    
    # التعامل مع طلبات الأحلام
    if re.search(r'هل تحلم|عن ماذا حلمت|ماذا حلمت|حلمت بماذا|أخبرني عن حلمك|حكي لي عن حلمك', message, re.IGNORECASE):
        dream = bot_memory.get_latest_dream()
        response = dream
        response = personalities.format_response(response, current_personality)
        conversation_context.add_message(user_id, response, sender='bot')
        return response
    
    # التعامل مع طلبات قصة الحياة
    if re.search(r'من أنت|عرف عن نفسك|أخبرني عن نفسك|ما هي قصتك|ما قصتك|حكي لي قصتك', message, re.IGNORECASE):
        life_story = bot_memory.get_life_story()
        response = life_story
        response = personalities.format_response(response, current_personality)
        conversation_context.add_message(user_id, response, sender='bot')
        return response
    
    # التعامل مع طلبات الذكريات
    if re.search(r'ماذا فعلت اليوم|بماذا قمت اليوم|ماذا فعلت|ماذا تتذكر', message, re.IGNORECASE):
        memory = bot_memory.create_daily_log()
        response = memory
        response = personalities.format_response(response, current_personality)
        conversation_context.add_message(user_id, response, sender='bot')
        return response
    
    # ---------------- معالجة الرسالة العادية ----------------
    
    # الحصول على سياق المحادثة
    context = conversation_context.get_context(user_id)
    
    # محاولة العثور على تطابق دقيق أو مشابه
    responses = firebase_db.get_all_responses()
    
    # تطابق دقيق
    if normalized_message in responses:
        base_response = responses[normalized_message]
        
        # تحقق من احتمالية تفعيل أحد ميزات الذاكرة
        enhanced_response = enhance_response_with_memory(base_response, user_id, current_personality)
        
        response = personalities.format_response(enhanced_response, current_personality)
        conversation_context.add_message(user_id, response, sender='bot')
        return response
    
    # محاولة العثور على تطابق باستخدام سياق المحادثة
    if context.get('related_to_previous') and context.get('last_topic'):
        # البحث عن ردود متعلقة بالسياق
        context_response = get_context_aware_response(normalized_message, context, responses)
        if context_response:
            # تعزيز الرد بميزات الذاكرة
            enhanced_response = enhance_response_with_memory(context_response, user_id, current_personality)
            
            response = personalities.format_response(enhanced_response, current_personality)
            conversation_context.add_message(user_id, response, sender='bot')
            return response
    
    # البحث عن تطابق مشابه
    best_match = None
    highest_similarity = 0
    
    for stored_message, response in responses.items():
        similarity = nlp_processor.calculate_similarity(normalized_message, stored_message)
        if similarity > highest_similarity and similarity >= SIMILARITY_THRESHOLD:
            highest_similarity = similarity
            best_match = response
    
    if best_match:
        # تعزيز الرد بميزات الذاكرة
        enhanced_response = enhance_response_with_memory(best_match, user_id, current_personality)
        
        response = personalities.format_response(enhanced_response, current_personality)
        conversation_context.add_message(user_id, response, sender='bot')
        return response
    
    # إذا لم يتم العثور على تطابق، نستخدم رد افتراضي مع الشخصية المحددة
    unknown_response = personalities.get_response_style("", current_personality, 'unknown')
    
    # تعزيز الرد بميزات الذاكرة
    enhanced_response = enhance_response_with_memory(unknown_response, user_id, current_personality)
    
    conversation_context.add_message(user_id, enhanced_response, sender='bot')
    return enhanced_response


def enhance_response_with_memory(base_response, user_id, personality_type):
    """
    تعزيز الرد الأساسي بميزات الذاكرة والشخصية
    
    Args:
        base_response (str): الرد الأساسي
        user_id (str): معرف المستخدم
        personality_type (str): نوع الشخصية
        
    Returns:
        str: الرد المعزز
    """
    response = base_response
    memory_triggered = False
    
    # إضافة المزاج إذا تفعلت الاحتمالية
    if random.random() < MOOD_TRIGGER_CHANCE:
        mood = bot_memory.get_current_mood()
        mood_prefix = f"[{mood['name']} {mood['emoji']}] "
        response = mood_prefix + response
        memory_triggered = True
    
    # إضافة ذكرى اللقاء الأول إذا تفعلت الاحتمالية
    if not memory_triggered and random.random() < MEMORY_TRIGGER_CHANCE:
        # التحقق من عدد التفاعلات (لتجنب ذكر هذا في المحادثات الأولى)
        if user_settings[user_id].get('interaction_count', 0) > 5:
            memory_statement = bot_memory.remember_first_meeting(user_id)
            response = response + f"\n\n{memory_statement}"
            memory_triggered = True
    
    # إضافة المشاعر تجاه كلمات معينة إذا تفعلت الاحتمالية
    if not memory_triggered and random.random() < EMOTION_TRIGGER_CHANCE:
        emotion_statement = bot_memory.get_emotional_response()
        response = response + f"\n\n{emotion_statement}"
        memory_triggered = True
    
    # إضافة حلم عشوائي إذا تفعلت الاحتمالية
    if not memory_triggered and random.random() < DREAM_TRIGGER_CHANCE:
        dream_prefix = "بالمناسبة، "
        if personality_type == 'مرح':
            dream_prefix = "تعرف؟ البارحة "
        elif personality_type == 'جدي':
            dream_prefix = "لقد حلمت البارحة بـ"
        elif personality_type == 'ساخر':
            dream_prefix = "هذا يذكرني بحلم غريب رأيته: "
        elif personality_type == 'حكيم':
            dream_prefix = "في منامي رأيت: "
        elif personality_type == 'عصبي':
            dream_prefix = "رأيت حلماً مزعجاً: "
            
        dream = bot_memory.get_latest_dream()
        response = response + f"\n\n{dream_prefix}{dream}"
    
    return response

def get_context_aware_response(message, context, responses):
    """
    البحث عن رد مناسب للسياق
    
    Args:
        message (str): رسالة المستخدم
        context (dict): سياق المحادثة
        responses (dict): قاموس الردود
        
    Returns:
        str: الرد المناسب للسياق أو None
    """
    # التعامل مع سياق توصيل أو مكان بعد سؤال عن السعر
    if context.get('last_topic') == 'توصيل' and context.get('product'):
        product = context.get('product')
        # البحث عن ردود تتعلق بتوصيل هذا المنتج
        pattern = f"توصيل {product}|تسليم {product}|مكان {product}"
        for stored_message, response in responses.items():
            if re.search(pattern, stored_message, re.IGNORECASE):
                return response
        
        # رد افتراضي عن التوصيل
        return f"يمكنك استلام {product} من مقر الشركة أو توصيله عبر خدمة التوصيل المتوفرة لدينا."
    
    return None

def add_response(message, response, user_id=None):
    """
    إضافة زوج رسالة-رد جديد إلى معرفة البوت
    
    Args:
        message (str): رسالة المستخدم
        response (str): الرد المرتبط بالرسالة
        user_id (str): معرف المستخدم (اختياري)
    """
    normalized_message = nlp_processor.preprocess_arabic_text(message)
    normalized_response = nlp_processor.preprocess_arabic_text(response)
    
    if normalized_message and normalized_response:
        # حفظ الرد في Firebase
        firebase_db.save_response(normalized_message, normalized_response)
        
        # إضافة الرد إلى سياق المحادثة إذا كان معرف المستخدم متوفراً
        if user_id:
            conversation_context.add_message(user_id, normalized_response, sender='bot', 
                                            metadata={'learned': True, 'original_message': message})
        return True
    return False

def get_greeting(user_id=None, personality_type=None):
    """
    الحصول على تحية عشوائية حسب شخصية البوت
    
    Args:
        user_id (str): معرف المستخدم (اختياري)
        personality_type (str): نوع شخصية البوت (اختياري)
        
    Returns:
        str: تحية عشوائية
    """
    # إنشاء معرف للمستخدم إذا لم يكن موجوداً
    if not user_id:
        user_id = str(uuid.uuid4())
    
    # التأكد من وجود إعدادات للمستخدم
    if user_id not in user_settings:
        user_settings[user_id] = {
            'personality': personality_type or 'مرح',
            'last_interaction': time.time()
        }
    
    # تحديث شخصية البوت إذا تم تحديدها
    if personality_type:
        user_settings[user_id]['personality'] = personality_type
    
    # الحصول على شخصية البوت الحالية
    current_personality = user_settings[user_id].get('personality', 'مرح')
    
    # الحصول على تحية من وحدة الشخصيات
    greeting = personalities.get_greeting(current_personality)
    
    # إضافة التحية إلى سياق المحادثة
    if user_id:
        conversation_context.add_message(user_id, greeting, sender='bot')
    
    return greeting

def get_user_personality(user_id):
    """
    الحصول على شخصية البوت المستخدمة مع المستخدم
    
    Args:
        user_id (str): معرف المستخدم
        
    Returns:
        str: نوع الشخصية
    """
    return user_settings.get(user_id, {}).get('personality', 'مرح')

def set_user_personality(user_id, personality_type):
    """
    تعيين شخصية البوت للمستخدم
    
    Args:
        user_id (str): معرف المستخدم
        personality_type (str): نوع الشخصية
    """
    if personality_type in personalities.get_available_personalities():
        if user_id not in user_settings:
            user_settings[user_id] = {'last_interaction': time.time()}
        user_settings[user_id]['personality'] = personality_type
        return True
    return False
