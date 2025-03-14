from flask import Flask, render_template, request, jsonify, session
import os
import chatbot
import firebase_db
import nlp_processor
import conversation_context
import personalities
import uuid
import json
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'salot_chatbot_secret_key')
app.permanent_session_lifetime = timedelta(days=30)

# مزامنة الردود المحلية مع Firebase عند بدء التطبيق
firebase_db.sync_responses()

@app.route('/')
def index():
    """عرض الصفحة الرئيسية لتطبيق الشات بوت."""
    # إنشاء معرف للمستخدم إذا لم يكن موجوداً
    if 'user_id' not in session:
        session.permanent = True
        session['user_id'] = str(uuid.uuid4())
        session['personality'] = 'مرح'  # شخصية افتراضية
    
    # الحصول على قائمة الشخصيات لإرسالها إلى الواجهة
    personalities_list = personalities.get_available_personalities()
    
    # استخدام التحية من شخصية البوت المحددة
    greeting = chatbot.get_greeting(session['user_id'], session['personality'])
    
    return render_template('index.html', greeting=greeting, personalities=personalities_list, current_personality=session['personality'])

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    API endpoint to handle chat requests.
    
    Expects a JSON with:
    - message: User's message
    - is_learning: Boolean indicating if this is a learning response
    - original_message: If learning, the original message this is responding to
    - personality: Optional - change the bot's personality
    """
    try:
        # التأكد من وجود معرف للمستخدم
        if 'user_id' not in session:
            session.permanent = True
            session['user_id'] = str(uuid.uuid4())
            session['personality'] = 'مرح'  # شخصية افتراضية
            
        user_id = session['user_id']
        data = request.json
        message = data.get('message', '').strip()
        
        # التعامل مع تغيير الشخصية
        personality = data.get('personality')
        if personality and personality in personalities.get_available_personalities():
            session['personality'] = personality
            chatbot.set_user_personality(user_id, personality)
            greeting = chatbot.get_greeting(user_id, personality)
            return jsonify({
                'response': greeting,
                'status': 'personality_changed',
                'personality': personality
            })
        
        # التعامل مع ردود التعلم
        if data.get('is_learning', False):
            original_message = data.get('original_message', '')
            if original_message and message:
                chatbot.add_response(original_message, message, user_id)
                return jsonify({
                    'response': 'تم حفظ الرد، شكراً!',
                    'status': 'learned'
                })
            else:
                return jsonify({
                    'response': 'حدث خطأ في حفظ الرد. الرجاء المحاولة مرة أخرى.',
                    'status': 'error'
                })
        
        # التأكد من وجود رسالة
        if not message:
            return jsonify({
                'response': 'لم أفهم رسالتك. الرجاء المحاولة مرة أخرى.',
                'status': 'error'
            })
        
        # الحصول على رد من البوت مع مراعاة الشخصية
        personality_type = session.get('personality', 'مرح')
        response = chatbot.get_response(message, user_id, personality_type)
        
        # إذا كان هناك رد، نعيده
        if response:
            # استرجاع سياق المحادثة الحالي
            context = conversation_context.get_context(user_id)
            
            return jsonify({
                'response': response,
                'status': 'success',
                'context': context,
                'personality': personality_type
            })
        else:
            # إذا لم يكن هناك رد، نطلب من المستخدم تعليم البوت
            return jsonify({
                'response': 'لا أعرف إجابة لهذا السؤال. هل يمكنك تعليمي الإجابة المناسبة؟',
                'status': 'unknown',
                'original_message': message,
                'personality': personality_type
            })
            
    except Exception as e:
        print(f"خطأ في معالجة الطلب: {str(e)}")
        return jsonify({
            'response': 'حدث خطأ في معالجة طلبك. الرجاء المحاولة مرة أخرى.',
            'status': 'error'
        })

@app.route('/api/personalities', methods=['GET'])
def get_personalities():
    """
    الحصول على قائمة الشخصيات المتاحة
    """
    try:
        return jsonify({
            'personalities': personalities.get_available_personalities(),
            'current': session.get('personality', 'مرح')
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/conversation', methods=['GET'])
def get_conversation():
    """
    الحصول على سجل المحادثة للمستخدم الحالي
    """
    try:
        if 'user_id' not in session:
            return jsonify({
                'error': 'لا يوجد جلسة نشطة'
            }), 400
            
        user_id = session['user_id']
        history = conversation_context.get_conversation_history(user_id)
        
        return jsonify({
            'history': history,
            'user_id': user_id
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
