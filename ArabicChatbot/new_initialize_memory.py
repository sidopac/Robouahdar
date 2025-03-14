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
                
                # دمج البيانات المحملة مع القيم الافتراضية
                BOT_MEMORY.update(loaded_memory)
                
                # تحويل التواريخ من النصوص إلى كائنات datetime
                if isinstance(BOT_MEMORY.get('creation_date'), str):
                    BOT_MEMORY['creation_date'] = datetime.datetime.fromisoformat(BOT_MEMORY['creation_date'])
                
                if isinstance(BOT_MEMORY.get('last_restart'), str):
                    BOT_MEMORY['last_restart'] = datetime.datetime.fromisoformat(BOT_MEMORY['last_restart'])
                
                if 'life_story' in BOT_MEMORY and isinstance(BOT_MEMORY['life_story'].get('story_date'), str):
                    BOT_MEMORY['life_story']['story_date'] = datetime.datetime.fromisoformat(BOT_MEMORY['life_story']['story_date'])
                
                # تحويل المجموعات من القوائم
                if 'conversation_stats' in BOT_MEMORY and 'users_encountered' in BOT_MEMORY['conversation_stats']:
                    BOT_MEMORY['conversation_stats']['users_encountered'] = set(BOT_MEMORY['conversation_stats']['users_encountered'])
                
                if 'life_story' in BOT_MEMORY and 'characters' in BOT_MEMORY['life_story']:
                    BOT_MEMORY['life_story']['characters'] = set(BOT_MEMORY['life_story']['characters'])
                
                # تحميل البيانات العاطفية
                if 'emotional_memory' in BOT_MEMORY:
                    emotional_memory = defaultdict(int)
                    for key, value in BOT_MEMORY['emotional_memory'].items():
                        emotional_memory[key] = value
                    BOT_MEMORY['emotional_memory'] = emotional_memory
                
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
    if not BOT_MEMORY.get('daily_mood'):
        set_daily_mood()
    
    # إنشاء حلم جديد إذا لم يكن هناك أحلام
    if not BOT_MEMORY.get('dreams'):
        generate_new_dream()
    
    # تحديث قصة الحياة إذا لزم الأمر
    if not BOT_MEMORY['life_story'].get('current_story'):
        new_story = "ولدت للتو! أنا بوت محادثة عربي ذكي اسمي صالوت (Salot). أنا متحمس للتعلم والتطور من خلال المحادثات مع الناس!"
        BOT_MEMORY['life_story']['current_story'] = new_story
        BOT_MEMORY['life_story']['story_date'] = datetime.datetime.now()
    
    # حفظ الذاكرة المحدثة
    save_memory()
