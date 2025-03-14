"""
Firebase Database Module for Arabic Learning Chatbot
Handles Firebase initialization and database operations
"""
import json
import os
import firebase_admin
from firebase_admin import credentials, firestore

# تهيئة Firebase باستخدام بيانات الاعتماد
try:
    firebase_config = os.environ.get('FIREBASE_CONFIG')
    if firebase_config:
        cred_dict = json.loads(firebase_config)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        
        # إنشاء مثيل لقاعدة البيانات
        db = firestore.client()
        responses_collection = db.collection('responses')
        print("تم الاتصال بـ Firebase بنجاح!")
    else:
        print("لم يتم العثور على تكوين Firebase")
except Exception as e:
    print(f"خطأ في تهيئة Firebase: {str(e)}")
    # استخدام متغيرات فارغة عند فشل الاتصال
    db = None
    responses_collection = None

def save_response(message, response):
    """
    حفظ رد جديد في قاعدة بيانات Firebase
    
    Args:
        message (str): رسالة المستخدم
        response (str): رد البوت
    """
    try:
        if responses_collection:
            doc_ref = responses_collection.document()
            doc_ref.set({
                'message': message,
                'response': response,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            print(f"تم حفظ الرد في Firebase: {message}")
            return True
        else:
            # استخدام التخزين المحلي كبديل
            print("استخدام التخزين المحلي بسبب عدم توفر Firebase")
            from storage import get_responses, save_responses
            responses = get_responses()
            responses[message] = response
            save_responses(responses)
            return True
    except Exception as e:
        print(f"خطأ في حفظ الرد: {str(e)}")
        # استخدام التخزين المحلي كبديل
        try:
            from storage import get_responses, save_responses
            responses = get_responses()
            responses[message] = response
            save_responses(responses)
            return True
        except Exception as inner_e:
            print(f"فشل في استخدام التخزين المحلي: {str(inner_e)}")
            return False

def get_all_responses():
    """
    استرجاع جميع الردود من قاعدة البيانات أو التخزين المحلي
    
    Returns:
        dict: قاموس يحتوي على الرسائل والردود
    """
    try:
        if responses_collection:
            responses = {}
            docs = responses_collection.stream()
            for doc in docs:
                data = doc.to_dict()
                if 'message' in data and 'response' in data:
                    responses[data['message']] = data['response']
            print(f"تم استرجاع {len(responses)} رد من Firebase")
            
            # إذا لم نجد أي ردود في Firebase، نستخدم التخزين المحلي
            if not responses:
                from storage import get_responses
                responses = get_responses()
                print(f"تم استرجاع {len(responses)} رد من التخزين المحلي")
            
            return responses
        else:
            # استخدام التخزين المحلي كبديل
            print("استخدام التخزين المحلي بسبب عدم توفر Firebase")
            from storage import get_responses
            return get_responses()
    except Exception as e:
        print(f"خطأ في استرجاع الردود: {str(e)}")
        # استخدام التخزين المحلي كبديل
        try:
            from storage import get_responses
            return get_responses()
        except Exception as inner_e:
            print(f"فشل في استخدام التخزين المحلي: {str(inner_e)}")
            return {}

def sync_responses():
    """
    مزامنة الردود المحلية مع Firebase
    """
    try:
        from storage import get_responses
        local_responses = get_responses()
        for message, response in local_responses.items():
            save_response(message, response)
        return True
    except Exception as e:
        print(f"Error syncing responses: {str(e)}")
        return False

def save_conversation_session(user_id, conversation, context):
    """
    حفظ جلسة محادثة في قاعدة بيانات Firebase
    
    Args:
        user_id (str): معرف المستخدم
        conversation (list): سجل المحادثة
        context (dict): سياق المحادثة
    """
    try:
        if not responses_collection:
            print("استخدام التخزين المحلي بسبب عدم توفر Firebase")
            return False
            
        # إنشاء مجموعة للمحادثات إذا لم تكن موجودة
        conversations_collection = db.collection('conversations')
        
        # حفظ المحادثة في وثيقة بمعرف المستخدم
        doc_ref = conversations_collection.document(user_id)
        
        # حفظ البيانات
        doc_ref.set({
            'user_id': user_id,
            'last_updated': firestore.SERVER_TIMESTAMP,
            'conversation': conversation,
            'context': context
        })
        
        print(f"تم حفظ جلسة المحادثة للمستخدم {user_id} في Firebase")
        return True
    except Exception as e:
        print(f"خطأ في حفظ جلسة المحادثة: {str(e)}")
        return False
        
def get_conversation_session(user_id):
    """
    استرجاع جلسة محادثة من قاعدة بيانات Firebase
    
    Args:
        user_id (str): معرف المستخدم
        
    Returns:
        tuple: (conversation, context) أو (None, None) في حالة عدم وجود بيانات
    """
    try:
        if not responses_collection:
            print("استخدام التخزين المحلي بسبب عدم توفر Firebase")
            return None, None
            
        # الوصول إلى مجموعة المحادثات
        conversations_collection = db.collection('conversations')
        
        # الحصول على وثيقة المستخدم
        doc_ref = conversations_collection.document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            return data.get('conversation', []), data.get('context', {})
        else:
            return [], {}
    except Exception as e:
        print(f"خطأ في استرجاع جلسة المحادثة: {str(e)}")
        return [], {}