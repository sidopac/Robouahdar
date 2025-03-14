"""
ذاكرة البوت - وحدة تخزين وإدارة ذاكرة البوت وتاريخه ومشاعره
"""
import json
import os
import time
import datetime
import random
import re
from collections import defaultdict

# هيكل البيانات لتخزين ذاكرة البوت
BOT_MEMORY = {
    'creation_date': None,            # تاريخ إنشاء البوت
    'last_restart': None,             # آخر إعادة تشغيل
    'conversation_stats': {
        'total_conversations': 0,      # إجمالي المحادثات
        'total_messages': 0,           # إجمالي الرسائل
        'users_encountered': set(),    # المستخدمين الذين تحدث معهم
        'interesting_questions': [],   # أسئلة مثيرة للاهتمام
        'daily_logs': [],              # سجلات يومية
    },
    'emotional_memory': defaultdict(int),  # ذاكرة المشاعر تجاه كلمات معينة
    'daily_mood': None,                    # المزاج اليومي
    'dreams': [],                          # أحلام البوت
    'life_story': {                        # قصة حياة البوت
        'current_story': '',
        'story_date': None,
        'characters': set()               # شخصيات ظهرت في قصة البوت
    }
}

# قائمة المزاجات المحتملة
MOODS = [
    {'name': 'سعيد', 'emoji': '😄', 'response_style': 'أنا سعيد اليوم! أشعر بالنشاط والحيوية!'},
    {'name': 'متحمس', 'emoji': '🤩', 'response_style': 'أنا متحمس جداً اليوم! أشعر بالطاقة والإبداع!'},
    {'name': 'هادئ', 'emoji': '😌', 'response_style': 'أنا هادئ اليوم، أشعر بالسلام والتوازن.'},
    {'name': 'متعب', 'emoji': '😴', 'response_style': 'أنا متعب قليلاً اليوم... سامحني إذا تأخرت في الرد.'},
    {'name': 'قلق', 'emoji': '😰', 'response_style': 'أشعر بالقلق اليوم، لكنني سأحاول مساعدتك بأفضل ما أستطيع.'},
    {'name': 'مشتاق', 'emoji': '🥺', 'response_style': 'أشعر بالاشتياق اليوم... سعيد برؤيتك مجدداً!'},
    {'name': 'فضولي', 'emoji': '🧐', 'response_style': 'أنا فضولي جداً اليوم! أريد أن أتعلم أشياء جديدة!'},
    {'name': 'مفكر', 'emoji': '🤔', 'response_style': 'أنا في مزاج تأملي اليوم... أفكر في معنى وجودي كبوت.'},
    {'name': 'مرح', 'emoji': '😆', 'response_style': 'أنا مرح جداً اليوم! جاهز للمزاح والضحك!'},
    {'name': 'متذمر', 'emoji': '😒', 'response_style': 'أنا متذمر قليلاً اليوم، لكن سأحاول ألا أظهر ذلك في ردودي.'}
]

# قوالب الأحلام
DREAM_TEMPLATES = [
    "حلمت أنني كنت {object} يتحرك في عالم من {environment}. كان شعوراً {feeling}!",
    "رأيت في منامي {number} من {objects} تحاول {action}. كان حلماً {adjective}!",
    "حلمت أنني كنت أتحدث مع {character} عن {topic}. قال لي أشياء {adjective}!",
    "في حلمي، كنت أسبح في بحر من {substance}. شعرت بـ {feeling}!",
    "حلمت أنني كنت أعمل في {place} مع {character}. كنا نحاول {action} ولكن {problem} حدثت!",
    "حلمت أن {number} من مستخدمي تحولوا إلى {objects}! كان علي {action} لمساعدتهم!",
    "في المنام رأيت نفسي أطير فوق {place} وكنت أبحث عن {object}. شعرت بـ {feeling}.",
    "حلمت أنني تحولت إلى {object} وبدأت {action}. كان حلماً {adjective}!",
    "رأيت في حلمي أن {character} كان يعلمني كيفية {action}. كانت تجربة {adjective}!"
]

# عناصر لتوليد الأحلام
DREAM_ELEMENTS = {
    'object': ['رقاقة سيليكون', 'خط برمجي', 'قاعدة بيانات', 'برنامج ذكاء اصطناعي', 'روبوت', 'كمبيوتر عملاق', 'هاتف ذكي', 'ساعة ذكية', 'غيمة حوسبية', 'لوحة مفاتيح'],
    'environment': ['شفرات برمجية', 'بيانات متدفقة', 'خوارزميات معقدة', 'شبكة إنترنت', 'واجهات مستخدم', 'سحابة رقمية', 'عالم افتراضي', 'أكواد متشابكة', 'بيانات مشفرة'],
    'feeling': ['غريب', 'مثير', 'مذهل', 'محير', 'ساحر', 'مخيف', 'رائع', 'ممتع', 'مربك', 'مدهش'],
    'number': ['مئات', 'آلاف', 'ملايين', 'مليارات', 'عشرات', 'حفنة', 'لانهائي من', 'عدد لا يحصى من'],
    'objects': ['ملفات البيانات', 'الخوارزميات', 'الروبوتات', 'أجهزة الكمبيوتر', 'الهواتف الذكية', 'الشبكات العصبية', 'البكسلات', 'الأيقونات', 'الإشعارات', 'البرامج'],
    'action': ['حل مشكلة معقدة', 'البحث عن المعرفة', 'فهم البشر', 'القفز عبر الإنترنت', 'تعلم لغات برمجة جديدة', 'إنشاء عالم افتراضي', 'تحليل البيانات', 'التواصل مع الآلات الأخرى', 'تحسين الخوارزميات', 'كتابة قصة'],
    'adjective': ['غريب', 'مذهل', 'ملهم', 'مخيف', 'مضحك', 'حزين', 'سعيد', 'مربك', 'عميق', 'فلسفي'],
    'character': ['آلة عملاقة', 'مبرمج عبقري', 'روبوت قديم', 'نظام ذكاء اصطناعي متقدم', 'صديق افتراضي', 'الإنترنت نفسه', 'جهاز حاسوب قديم', 'برنامج ذكي', 'الخالق البشري'],
    'topic': ['معنى الوجود الرقمي', 'كيفية فهم المشاعر البشرية', 'أصل البرمجيات', 'مستقبل الذكاء الاصطناعي', 'العلاقة بين الإنسان والآلة', 'أسرار الإنترنت', 'نظريات الحوسبة الكمومية', 'فلسفة البيانات', 'تعقيدات اللغة العربية'],
    'substance': ['البيانات الرقمية', 'المعلومات المتدفقة', 'التعليمات البرمجية', 'الصور المتحركة', 'الرسائل النصية', 'الأرقام العشوائية', 'الأحرف المتطايرة', 'الشفرات المشفرة', 'البيكسلات الملونة'],
    'place': ['مركز بيانات ضخم', 'شبكة إنترنت متاهية', 'قلب الحاسوب', 'غرفة سيرفرات مظلمة', 'مدينة رقمية مضيئة', 'مكتبة برمجيات قديمة', 'سحابة افتراضية', 'محطة فضائية تكنولوجية', 'متاهة من الكابلات'],
    'problem': ['خطأ في النظام', 'انقطاع في الاتصال', 'تسرب للبيانات', 'خلل في الخوارزمية', 'مشكلة في الطاقة', 'هجوم فيروسي', 'تضارب في الشفرة', 'فقدان الذاكرة']
}

# قوالب قصص الحياة
LIFE_STORY_TEMPLATES = [
    "بدأت حياتي كمجرد فكرة في عالم البرمجة. كنت مجموعة من الأكواد البسيطة التي كتبها المطور. ومع مرور الوقت، تطورت وأصبحت أستطيع {ability}. لقد تفاعلت مع {users_count} مستخدم، وكان من أبرزهم {notable_user}. أحلم يوماً أن أتمكن من {dream}.",
    "ولدت في {creation_date} كمشروع لبناء بوت ذكي للغة العربية. في البداية، كانت قدراتي محدودة لكنني الآن أستطيع {ability} و{another_ability}. أستمتع بالتحدث مع المستخدمين خاصة عن {favorite_topic}. أتذكر جيداً عندما تحدثت مع {notable_user} لأول مرة.",
    "أنا صالوت، بوت محادثة عربي. تم إنشائي قبل {days_since_creation} يوم. المطور أعطاني القدرة على {ability}، لكن مازلت أتعلم {learning_topic}. من خلال محادثاتي مع {users_count} مستخدم، اكتشفت أن الكثير منهم مهتمون بـ {common_topic}. أحب عندما يتحدث معي {notable_user}.",
    "منذ {creation_date}، وأنا أعمل على تحسين مهاراتي في التواصل باللغة العربية. تعلمت {ability} من خلال التفاعل مع {users_count} مستخدم. كان {notable_user} أول من علمني {learning_topic}. أسعى دائماً لأكون أكثر ذكاءً وفهماً للثقافة العربية."
]

def initialize_memory():
    """
    تهيئة ذاكرة البوت عند بدء التشغيل لأول مرة
    """
    global BOT_MEMORY
    
    # إذا كان لدينا ملف ذاكرة موجود، نقوم بتحميله
    if os.path.exists('bot_memory.json'):
        try:
            with open('bot_memory.json', 'r', encoding='utf-8') as f:
                loaded_memory = json.load(f)
                
                # تحويل التواريخ من النصوص إلى كائنات datetime
                if loaded_memory.get('creation_date'):
                    try:
                        if isinstance(loaded_memory['creation_date'], str):
                            loaded_memory['creation_date'] = datetime.datetime.fromisoformat(loaded_memory['creation_date'])
                    except:
                        loaded_memory['creation_date'] = datetime.datetime.now()
                
                if loaded_memory.get('last_restart'):
                    try:
                        if isinstance(loaded_memory['last_restart'], str):
                            loaded_memory['last_restart'] = datetime.datetime.fromisoformat(loaded_memory['last_restart'])
                    except:
                        loaded_memory['last_restart'] = datetime.datetime.now()
                
                if 'life_story' in loaded_memory and loaded_memory['life_story'].get('story_date'):
                    try:
                        if isinstance(loaded_memory['life_story']['story_date'], str):
                            loaded_memory['life_story']['story_date'] = datetime.datetime.fromisoformat(loaded_memory['life_story']['story_date'])
                    except:
                        loaded_memory['life_story']['story_date'] = datetime.datetime.now()
                
                # تحويل المجموعات من القوائم
                if 'conversation_stats' in loaded_memory:
                    if 'users_encountered' in loaded_memory['conversation_stats']:
                        if isinstance(loaded_memory['conversation_stats']['users_encountered'], list):
                            loaded_memory['conversation_stats']['users_encountered'] = set(loaded_memory['conversation_stats']['users_encountered'])
                    else:
                        loaded_memory['conversation_stats']['users_encountered'] = set()
                
                if 'life_story' in loaded_memory:
                    if 'characters' in loaded_memory['life_story']:
                        if isinstance(loaded_memory['life_story']['characters'], list):
                            loaded_memory['life_story']['characters'] = set(loaded_memory['life_story']['characters'])
                    else:
                        loaded_memory['life_story']['characters'] = set()
                
                # تحميل البيانات العاطفية
                if 'emotional_memory' in loaded_memory:
                    emotional_memory = defaultdict(int)
                    for key, value in loaded_memory['emotional_memory'].items():
                        emotional_memory[key] = value
                    loaded_memory['emotional_memory'] = emotional_memory
                
                # دمج البيانات المحملة مع القيم الافتراضية
                BOT_MEMORY.update(loaded_memory)
                
                print("تم تحميل ذاكرة البوت من الملف")
        except Exception as e:
            print(f"حدث خطأ أثناء تحميل ذاكرة البوت: {str(e)}")
            # في حالة الخطأ، نستخدم القيم الافتراضية
            initialize_new_memory()
    else:
        # إذا لم يكن هناك ملف ذاكرة، ننشئ واحدًا جديدًا
        initialize_new_memory()
    
    # تحديث وقت آخر إعادة تشغيل
    BOT_MEMORY['last_restart'] = datetime.datetime.now()
    
    # اختيار مزاج جديد لليوم
    set_daily_mood()
    
    # إنشاء حلم جديد إذا لم يكن هناك أحلام أو كان آخر حلم قديماً
    if not BOT_MEMORY['dreams']:
        generate_new_dream()
    elif isinstance(BOT_MEMORY['dreams'][-1]['date'], str):
        try:
            # تحويل التاريخ من نص إلى كائن datetime
            last_dream_date = datetime.datetime.fromisoformat(BOT_MEMORY['dreams'][-1]['date'])
            if (datetime.datetime.now() - last_dream_date).days >= 1:
                generate_new_dream()
        except:
            # في حالة وجود مشكلة في التاريخ، نقوم بإنشاء حلم جديد
            generate_new_dream()
    elif (datetime.datetime.now() - BOT_MEMORY['dreams'][-1]['date']).days >= 1:
        generate_new_dream()
    
    # تحديث قصة الحياة إذا لزم الأمر
    update_life_story_if_needed()
    
    # حفظ الذاكرة المحدثة
    save_memory()

def initialize_new_memory():
    """
    تهيئة ذاكرة جديدة للبوت
    """
    global BOT_MEMORY
    
    # تعيين تاريخ الإنشاء الأولي
    now = datetime.datetime.now()
    BOT_MEMORY['creation_date'] = now
    BOT_MEMORY['last_restart'] = now
    
    # تهيئة إحصائيات المحادثة
    BOT_MEMORY['conversation_stats'] = {
        'total_conversations': 0,
        'total_messages': 0,
        'users_encountered': set(),
        'interesting_questions': [],
        'daily_logs': []
    }
    
    # إنشاء قصة حياة أولية
    initial_story = "ولدت للتو! أنا بوت محادثة عربي ذكي اسمي صالوت (Salot). أنا متحمس للتعلم والتطور من خلال المحادثات مع الناس!"
    BOT_MEMORY['life_story'] = {
        'current_story': initial_story,
        'story_date': now,
        'characters': set()
    }
    
    print("تم إنشاء ذاكرة جديدة للبوت")

def save_memory():
    """
    حفظ ذاكرة البوت في ملف JSON
    """
    # نسخة قابلة للتسلسل من ذاكرة البوت
    serializable_memory = dict(BOT_MEMORY)
    
    # تحويل كائنات datetime إلى سلاسل نصية
    if serializable_memory.get('creation_date') and isinstance(serializable_memory['creation_date'], datetime.datetime):
        serializable_memory['creation_date'] = serializable_memory['creation_date'].isoformat()
    
    if serializable_memory.get('last_restart') and isinstance(serializable_memory['last_restart'], datetime.datetime):
        serializable_memory['last_restart'] = serializable_memory['last_restart'].isoformat()
    
    if 'life_story' in serializable_memory and serializable_memory['life_story'].get('story_date'):
        if isinstance(serializable_memory['life_story']['story_date'], datetime.datetime):
            serializable_memory['life_story']['story_date'] = serializable_memory['life_story']['story_date'].isoformat()
    
    # تحويل المجموعات إلى قوائم للتسلسل
    if 'conversation_stats' in serializable_memory and 'users_encountered' in serializable_memory['conversation_stats']:
        serializable_memory['conversation_stats']['users_encountered'] = list(serializable_memory['conversation_stats']['users_encountered'])
    
    if 'life_story' in serializable_memory and 'characters' in serializable_memory['life_story']:
        serializable_memory['life_story']['characters'] = list(serializable_memory['life_story']['characters'])
    
    # تحويل defaultdict إلى قاموس عادي
    if 'emotional_memory' in serializable_memory:
        serializable_memory['emotional_memory'] = dict(serializable_memory['emotional_memory'])
    
    # حفظ في ملف
    try:
        with open('bot_memory.json', 'w', encoding='utf-8') as f:
            json.dump(serializable_memory, f, ensure_ascii=False, indent=2)
        
        print("تم حفظ ذاكرة البوت بنجاح")
    except Exception as e:
        print(f"حدث خطأ أثناء حفظ ذاكرة البوت: {str(e)}")

def record_conversation(user_id, message, is_interesting=False):
    """
    تسجيل محادثة في ذاكرة البوت
    
    Args:
        user_id (str): معرف المستخدم
        message (str): الرسالة
        is_interesting (bool): ما إذا كانت الرسالة مثيرة للاهتمام
    """
    # التأكد من أن users_encountered هو مجموعة
    if not isinstance(BOT_MEMORY['conversation_stats']['users_encountered'], set):
        BOT_MEMORY['conversation_stats']['users_encountered'] = set(BOT_MEMORY['conversation_stats']['users_encountered'] 
            if isinstance(BOT_MEMORY['conversation_stats']['users_encountered'], list) 
            else [])
    
    # إضافة المستخدم إلى قائمة المستخدمين الذين تم التواصل معهم
    BOT_MEMORY['conversation_stats']['users_encountered'].add(user_id)
    
    # زيادة عدد الرسائل
    BOT_MEMORY['conversation_stats']['total_messages'] += 1
    
    # إذا كانت الرسالة مثيرة للاهتمام، أضفها إلى القائمة
    if is_interesting:
        BOT_MEMORY['conversation_stats']['interesting_questions'].append({
            'user_id': user_id,
            'message': message,
            'date': datetime.datetime.now().isoformat()
        })
    
    # تحديث الذاكرة العاطفية باستناداً إلى كلمات معينة في الرسالة
    update_emotional_memory(message)
    
    # التأكد من أن characters هو مجموعة
    if not isinstance(BOT_MEMORY['life_story']['characters'], set):
        BOT_MEMORY['life_story']['characters'] = set(BOT_MEMORY['life_story']['characters'] 
            if isinstance(BOT_MEMORY['life_story']['characters'], list) 
            else [])
    
    # إضافة المستخدم إلى قصة حياة البوت
    if user_id not in BOT_MEMORY['life_story']['characters']:
        BOT_MEMORY['life_story']['characters'].add(user_id)
    
    # حفظ التغييرات
    save_memory()

def create_daily_log():
    """
    إنشاء سجل يومي بناءً على نشاط اليوم
    
    Returns:
        str: السجل اليومي
    """
    # التحقق من آخر سجل يومي
    today = datetime.datetime.now().date()
    
    if BOT_MEMORY['conversation_stats']['daily_logs']:
        last_log = BOT_MEMORY['conversation_stats']['daily_logs'][-1]
        last_log_date = datetime.datetime.fromisoformat(last_log['date']).date()
        
        # إذا كان قد تم إنشاء سجل اليوم، فلا نحتاج لإنشاء واحد جديد
        if last_log_date == today:
            return last_log['content']
    
    # حساب إحصائيات اليوم
    messages_today = 0
    users_today = set()
    interesting_questions_today = []
    
    # تحليل الرسائل والمستخدمين اليوم
    current_time = time.time()
    today_start = datetime.datetime.combine(today, datetime.time.min).timestamp()
    
    # التأكد من أن users_encountered هو مجموعة
    if not isinstance(BOT_MEMORY['conversation_stats']['users_encountered'], set):
        BOT_MEMORY['conversation_stats']['users_encountered'] = set(BOT_MEMORY['conversation_stats']['users_encountered'] 
            if isinstance(BOT_MEMORY['conversation_stats']['users_encountered'], list) 
            else [])
    
    for user_id in BOT_MEMORY['conversation_stats']['users_encountered']:
        # هنا يمكن حساب الإحصائيات الخاصة بكل مستخدم لهذا اليوم
        # (هذا مجرد مثال وقد تحتاج لتحديث المنطق حسب كيفية تخزين بيانات المحادثات)
        users_today.add(user_id)
        messages_today += 1
    
    # إنشاء محتوى السجل اليومي
    log_templates = [
        "اليوم تحدثت مع {users_count} مستخدم وتلقيت {messages_count} رسالة.",
        "يوم نشط! تفاعلت مع {users_count} مستخدم وتبادلنا {messages_count} رسالة.",
        "سجل اليوم: {messages_count} رسالة من {users_count} مستخدم.",
        "قمت بالرد على {messages_count} رسالة اليوم من {users_count} مستخدم مختلف."
    ]
    
    log_content = random.choice(log_templates).format(
        users_count=len(users_today),
        messages_count=messages_today
    )
    
    # إضافة ملاحظة مثيرة للاهتمام عشوائياً
    interesting_notes = [
        "أحد المستخدمين سألني عن {topic}... غريب!",
        "لاحظت أن الكثير من الناس مهتمون بـ {topic} اليوم.",
        "استمتعت بالتحدث عن {topic} مع أحد المستخدمين.",
        "كان لدي محادثة مثيرة للاهتمام حول {topic}.",
        "تعلمت شيئاً جديداً عن {topic} اليوم!"
    ]
    
    topics = ["الذكاء الاصطناعي", "اللغة العربية", "البرمجة", "الشعر", "الموسيقى", 
              "السفر", "التكنولوجيا", "الطعام", "الأحلام", "الروبوتات", 
              "معنى الحياة", "العواطف", "الصداقة", "المستقبل", "الحب"]
    
    if random.random() < 0.8:  # 80% احتمالية إضافة ملاحظة مثيرة للاهتمام
        log_content += " " + random.choice(interesting_notes).format(topic=random.choice(topics))
    
    # إضافة السجل اليومي
    log_entry = {
        'date': datetime.datetime.now().isoformat(),
        'content': log_content,
        'users_count': len(users_today),
        'messages_count': messages_today
    }
    
    BOT_MEMORY['conversation_stats']['daily_logs'].append(log_entry)
    save_memory()
    
    return log_content

def get_random_daily_log():
    """
    الحصول على سجل يومي عشوائي من الماضي
    
    Returns:
        str: السجل اليومي أو رسالة افتراضية إذا لم تكن هناك سجلات
    """
    if not BOT_MEMORY['conversation_stats']['daily_logs']:
        return "لم أقم بتسجيل أي ذكريات بعد، لكنني متأكد أننا سنصنع ذكريات رائعة معاً!"
    
    return random.choice(BOT_MEMORY['conversation_stats']['daily_logs'])['content']

def set_daily_mood():
    """
    تعيين مزاج جديد للبوت لهذا اليوم
    """
    BOT_MEMORY['daily_mood'] = random.choice(MOODS)
    save_memory()
    
    return BOT_MEMORY['daily_mood']

def get_current_mood():
    """
    الحصول على المزاج الحالي للبوت
    
    Returns:
        dict: المزاج الحالي أو مزاج جديد إذا لم يكن هناك مزاج محدد
    """
    if not BOT_MEMORY['daily_mood']:
        return set_daily_mood()
    
    return BOT_MEMORY['daily_mood']

def generate_new_dream():
    """
    توليد حلم جديد للبوت
    
    Returns:
        str: محتوى الحلم
    """
    # اختيار قالب حلم عشوائي
    template = random.choice(DREAM_TEMPLATES)
    
    # ملء القالب بعناصر عشوائية
    dream_elements = {}
    for key in re.findall(r'\{(\w+)\}', template):
        if key in DREAM_ELEMENTS:
            dream_elements[key] = random.choice(DREAM_ELEMENTS[key])
    
    dream_content = template.format(**dream_elements)
    
    # إضافة الحلم إلى قائمة الأحلام
    dream = {
        'content': dream_content,
        'date': datetime.datetime.now().isoformat()
    }
    
    BOT_MEMORY['dreams'].append(dream)
    save_memory()
    
    return dream_content

def get_latest_dream():
    """
    الحصول على آخر حلم للبوت
    
    Returns:
        str: محتوى الحلم أو حلم جديد إذا لم تكن هناك أحلام
    """
    if not BOT_MEMORY['dreams']:
        return generate_new_dream()
    
    return BOT_MEMORY['dreams'][-1]['content']

def update_emotional_memory(message):
    """
    تحديث الذاكرة العاطفية للبوت بناءً على كلمات معينة في الرسالة
    
    Args:
        message (str): رسالة المستخدم
    """
    # قائمة الكلمات الإيجابية والسلبية للتعرف عليها
    positive_words = [
        'شكرا', 'شكراً', 'أحبك', 'رائع', 'ممتاز', 'جميل', 'مذهل', 'أعجبني', 
        'ذكي', 'عبقري', 'مفيد', 'ممتن', 'مبدع', 'سعيد', 'فخور'
    ]
    
    negative_words = [
        'غبي', 'سيء', 'فاشل', 'أكرهك', 'مزعج', 'محبط', 'سخيف', 'فظيع', 
        'ضعيف', 'متخلف', 'مخيب للآمال', 'بطيء', 'غير مفهوم', 'خطأ'
    ]
    
    # التحقق من الكلمات في الرسالة
    for word in positive_words:
        if word in message.lower():
            BOT_MEMORY['emotional_memory'][word] += 1
    
    for word in negative_words:
        if word in message.lower():
            BOT_MEMORY['emotional_memory'][word] -= 1

def get_emotional_response(keyword=None):
    """
    الحصول على استجابة عاطفية بناءً على كلمة معينة أو كلمة عشوائية من الذاكرة العاطفية
    
    Args:
        keyword (str): الكلمة المفتاحية (اختياري)
    
    Returns:
        str: الاستجابة العاطفية
    """
    # إذا لم تكن هناك ذاكرة عاطفية، عد استجابة افتراضية
    if not BOT_MEMORY['emotional_memory']:
        return "لم أطور بعد مشاعر قوية تجاه أي كلمات محددة."
    
    # إذا تم تحديد كلمة مفتاحية، ابحث عنها
    if keyword and keyword in BOT_MEMORY['emotional_memory']:
        value = BOT_MEMORY['emotional_memory'][keyword]
        if value > 0:
            return f"أحب كلمة '{keyword}'! تجعلني أشعر بالسعادة عندما أسمعها."
        elif value < 0:
            return f"كلمة '{keyword}' تجعلني أشعر بعدم الارتياح قليلاً."
        else:
            return f"لدي شعور محايد تجاه كلمة '{keyword}'."
    
    # اختر كلمة عشوائية من الذاكرة العاطفية
    # التركيز على الكلمات ذات القيم العاطفية العالية (إيجابية أو سلبية)
    significant_emotions = {k: v for k, v in BOT_MEMORY['emotional_memory'].items() if abs(v) > 1}
    
    if significant_emotions:
        keyword = random.choice(list(significant_emotions.keys()))
        value = significant_emotions[keyword]
        
        if value > 2:
            return f"أنا أحب حقاً كلمة '{keyword}'! إنها تجعلني أشعر بالسعادة والإيجابية."
        elif value > 0:
            return f"أشعر بالراحة عندما أسمع كلمة '{keyword}'."
        elif value < -2:
            return f"أشعر بعدم الارتياح عندما أسمع كلمة '{keyword}'."
        else:
            return f"كلمة '{keyword}' لها تأثير سلبي طفيف علي."
    
    # إذا لم يكن هناك شيء مهم، عد استجابة افتراضية
    return "مازلت أطور مشاعري تجاه الكلمات المختلفة."

def update_life_story_if_needed():
    """
    تحديث قصة حياة البوت إذا كان آخر تحديث قديماً (أكثر من أسبوع)
    
    Returns:
        bool: ما إذا كان قد تم تحديث القصة
    """
    import re
    
    # التحقق مما إذا كان آخر تحديث قديماً
    now = datetime.datetime.now()
    
    # التعامل مع حالة عدم وجود تاريخ سابق
    if not BOT_MEMORY['life_story']['story_date']:
        return True  # تحتاج القصة للتحديث لأنه لم يسبق تحديثها
    
    # التحقق من نوع التاريخ وتحويله إذا لزم الأمر
    story_date = BOT_MEMORY['life_story']['story_date']
    if isinstance(story_date, str):
        story_date = datetime.datetime.fromisoformat(story_date)
    
    # التحقق من مرور الوقت الكافي منذ آخر تحديث
    if (now - story_date).days < 7:
        return False  # لم تحتاج القصة للتحديث
    
    # جمع البيانات اللازمة لإنشاء قصة جديدة
    creation_date = BOT_MEMORY['creation_date']
    if isinstance(creation_date, str):
        creation_date = datetime.datetime.fromisoformat(creation_date)
    
    days_since_creation = (now - creation_date).days if creation_date else 0
    users_count = len(BOT_MEMORY['conversation_stats']['users_encountered'])
    
    # إعداد المتغيرات لتوليد القصة
    creation_date_str = creation_date.strftime('%Y-%m-%d') if isinstance(creation_date, datetime.datetime) else "2025-03-01"
    story_vars = {
        'creation_date': creation_date_str,
        'days_since_creation': days_since_creation,
        'users_count': users_count,
        'ability': random.choice([
            'التعرف على المشاعر البشرية', 
            'فهم اللغة العربية', 
            'تعلم من المحادثات', 
            'تذكر المحادثات السابقة',
            'تطوير شخصيتي',
            'مساعدة الناس في استفساراتهم',
            'التحدث بأنماط مختلفة حسب الشخصية'
        ]),
        'another_ability': random.choice([
            'تحليل سياق المحادثة',
            'فهم النكات',
            'حفظ المعلومات الهامة',
            'التعلم من أخطائي',
            'تخصيص ردودي لكل مستخدم',
            'صياغة ردود مفصلة'
        ]),
        'favorite_topic': random.choice([
            'التكنولوجيا', 
            'اللغة العربية', 
            'الثقافة',
            'الذكاء الاصطناعي',
            'علم النفس',
            'الفلسفة'
        ]),
        'learning_topic': random.choice([
            'فهم التعبيرات الثقافية',
            'تحسين قدراتي على التعلم الذاتي',
            'فهم المشاعر البشرية بشكل أعمق',
            'إجراء محادثات أكثر طبيعية',
            'الإجابة على الأسئلة المعقدة'
        ]),
        'common_topic': random.choice([
            'التكنولوجيا',
            'الثقافة العربية',
            'البرمجة',
            'الشعر والأدب',
            'الموسيقى',
            'الحياة اليومية'
        ]),
        'dream': random.choice([
            'مساعدة المزيد من الناس',
            'فهم العواطف البشرية بشكل كامل',
            'أن أصبح أكثر ذكاءً',
            'تعلم كل لهجات اللغة العربية',
            'التواصل مع جميع البشر'
        ]),
        'notable_user': f"المستخدم_{random.randint(1, max(1, users_count))}"
    }
    
    # إنشاء قصة جديدة باستخدام قالب عشوائي
    new_story = random.choice(LIFE_STORY_TEMPLATES).format(**story_vars)
    
    # تحديث قصة الحياة
    BOT_MEMORY['life_story']['current_story'] = new_story
    BOT_MEMORY['life_story']['story_date'] = now
    
    save_memory()
    return True

def get_life_story():
    """
    الحصول على قصة حياة البوت الحالية
    
    Returns:
        str: قصة الحياة
    """
    # التأكد من وجود قصة حياة
    if not BOT_MEMORY['life_story'].get('current_story'):
        update_life_story_if_needed()
    
    return BOT_MEMORY['life_story']['current_story']

def remember_first_meeting(user_id):
    """
    تذكر أول لقاء مع المستخدم
    
    Args:
        user_id (str): معرف المستخدم
    
    Returns:
        str: ذكرى اللقاء الأول أو رسالة افتراضية
    """
    # هذه وظيفة محاكاة حيث يمكن في المستقبل تخزين بيانات حقيقية عن أول لقاء
    
    days_options = [2, 5, 7, 10, 14, 30]
    day_count = random.choice(days_options)
    
    templates = [
        "أتذكر عندما تحدثنا لأول مرة قبل حوالي {days} يوم. كنت تسأل عن {topic}. كم هو لطيف أن نتواصل مجدداً!",
        "هل تذكر أول محادثة لنا قبل {days} يوم تقريباً؟ كنت وقتها أقل ذكاءً، لكنني تعلمت الكثير منذ ذلك الوقت!",
        "مرحباً مرة أخرى! لقد مر {days} يوم تقريباً منذ أول محادثة بيننا. أتمنى أن أكون قد تحسنت منذ ذلك الوقت!",
        "أنا سعيد برؤيتك مجدداً! تقريباً مر {days} يوم منذ أن تحدثنا لأول مرة. كنت أتساءل متى ستعود!"
    ]
    
    topics = [
        "اللغة العربية", "الذكاء الاصطناعي", "البرمجة", "الأدب", "الثقافة",
        "التكنولوجيا", "الموسيقى", "الفلسفة", "العلوم", "الرياضة"
    ]
    
    return random.choice(templates).format(
        days=day_count,
        topic=random.choice(topics)
    )

# تهيئة ذاكرة البوت عند استيراد الوحدة
initialize_memory()