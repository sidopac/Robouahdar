document.addEventListener('DOMContentLoaded', function() {
    // عناصر DOM الرئيسية
    const chatMessages = document.getElementById('chat-messages');
    const chatContext = document.getElementById('chat-context');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const learningContainer = document.getElementById('learning-container');
    const learningPrompt = document.getElementById('learning-prompt');
    const learningInput = document.getElementById('learning-input');
    const saveLearningButton = document.getElementById('save-learning');
    const cancelLearningButton = document.getElementById('cancel-learning');
    
    // عناصر DOM للشخصيات والإعدادات
    const settingsToggle = document.getElementById('settings-toggle');
    const settingsPanel = document.getElementById('settings-panel');
    const closeSettings = document.getElementById('close-settings');
    const personalityOptions = document.querySelectorAll('.personality-option');
    const currentPersonalityName = document.getElementById('current-personality-name');
    const currentPersonalityEmoji = document.getElementById('current-personality-emoji');
    
    // متغيرات الحالة
    let currentOriginalMessage = '';
    let isLearningMode = false;
    let currentPersonality = CURRENT_PERSONALITY || 'مرح';
    let contextData = {}; // لتخزين بيانات السياق
    
    // ترجمة الشخصيات إلى الإنجليزية للاستخدام في CSS
    const personalityMapping = {
        'مرح': 'fun',
        'جدي': 'serious',
        'ساخر': 'sarcastic',
        'حكيم': 'wise',
        'عصبي': 'angry'
    };
    
    // إظهار التحية الافتتاحية
    if (GREETING) {
        addMessage(GREETING, 'bot', currentPersonality);
    } else {
        addMessage('مرحباً بك في صالوت - بوت المحادثة العربي الذكي!', 'bot', currentPersonality);
    }
    
    addSystemMessage('يمكنك تعليمي إجابات جديدة عندما لا أعرف الإجابة 📝 ويمكنك تغيير شخصيتي من أيقونة الإعدادات ⚙️');

    // مستمعو الأحداث
    sendButton.addEventListener('click', handleSendMessage);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    
    saveLearningButton.addEventListener('click', handleLearningSubmit);
    cancelLearningButton.addEventListener('click', cancelLearningMode);
    
    // مستمعو أحداث الإعدادات
    settingsToggle.addEventListener('click', toggleSettings);
    closeSettings.addEventListener('click', toggleSettings);
    
    // مستمعو أحداث الشخصيات
    personalityOptions.forEach(option => {
        option.addEventListener('click', () => {
            const personality = option.getAttribute('data-personality');
            changePersonality(personality);
        });
    });
    
    // الوظائف الرئيسية
    function handleSendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        addMessage(message, 'user');
        userInput.value = '';
        
        // إذا كنا في وضع التعلم، تعامل مع تدفق التعلم
        if (isLearningMode) {
            showLearningMode(false);
            return;
        }
        
        // وإلا، أرسل الرسالة إلى واجهة برمجة التطبيقات
        sendMessageToAPI(message);
    }
    
    function sendMessageToAPI(message, options = {}) {
        // إظهار مؤشر الكتابة
        const typingIndicator = addTypingIndicator();
        
        // تحضير البيانات للإرسال
        const requestData = { 
            message: message,
            ...options
        };
        
        // إذا كان هناك تغيير في الشخصية، أضفها للطلب
        if (options.personality) {
            currentPersonality = options.personality;
        }
        
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            // إزالة مؤشر الكتابة
            if (typingIndicator) {
                typingIndicator.remove();
            }
            
            // معالجة الرد حسب الحالة
            if (data.status === 'success') {
                addMessage(data.response, 'bot', data.personality || currentPersonality);
                
                // إذا كان هناك سياق، قم بعرضه
                if (data.context && Object.keys(data.context).length > 0) {
                    updateContextDisplay(data.context);
                }
            } 
            else if (data.status === 'unknown') {
                addMessage(data.response, 'bot', data.personality || currentPersonality);
                currentOriginalMessage = data.original_message;
                showLearningMode(true);
            } 
            else if (data.status === 'personality_changed') {
                // تم تغيير الشخصية بنجاح
                currentPersonality = data.personality;
                updateCurrentPersonalityDisplay();
                addSystemMessage(`تم تغيير شخصية البوت إلى "${currentPersonality}"`);
                addMessage(data.response, 'bot', currentPersonality);
            } 
            else {
                addMessage(data.response || 'حدث خطأ في الاتصال، حاول مرة أخرى.', 'bot', currentPersonality);
            }
        })
        .catch(error => {
            // إزالة مؤشر الكتابة
            if (typingIndicator) {
                typingIndicator.remove();
            }
            console.error('Error:', error);
            addMessage('حدث خطأ في الاتصال، حاول مرة أخرى.', 'bot', currentPersonality);
        });
    }
    
    function handleLearningSubmit() {
        const learningResponse = learningInput.value.trim();
        if (!learningResponse) {
            alert('الرجاء إدخال إجابة لتعليم البوت');
            return;
        }
        
        showLearningMode(false);
        
        // إرسال بيانات التعلم إلى واجهة برمجة التطبيقات
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: learningResponse,
                is_learning: true,
                original_message: currentOriginalMessage
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'learned') {
                addSystemMessage('شكراً لتعليمي إجابة جديدة! 🎉');
            } else {
                addSystemMessage('حدث خطأ في حفظ الإجابة. 😕');
            }
            learningInput.value = '';
            currentOriginalMessage = '';
        })
        .catch(error => {
            console.error('Error:', error);
            addSystemMessage('حدث خطأ في حفظ الإجابة. 😕');
            learningInput.value = '';
            currentOriginalMessage = '';
        });
    }
    
    function cancelLearningMode() {
        showLearningMode(false);
        addSystemMessage('تم إلغاء التعلم.');
        learningInput.value = '';
        currentOriginalMessage = '';
    }
    
    function showLearningMode(show) {
        isLearningMode = show;
        
        if (show) {
            learningContainer.classList.remove('hidden');
            learningPrompt.textContent = 'علمني كيف أرد على: ' + currentOriginalMessage;
            learningInput.focus();
        } else {
            learningContainer.classList.add('hidden');
            userInput.focus();
        }
    }
    
    function toggleSettings() {
        settingsPanel.classList.toggle('hidden');
    }
    
    function changePersonality(personality) {
        if (personality === currentPersonality) {
            toggleSettings();
            return;
        }
        
        // تحديث العرض المرئي للشخصيات
        personalityOptions.forEach(option => {
            option.classList.toggle('active', option.getAttribute('data-personality') === personality);
        });
        
        // إرسال طلب تغيير الشخصية
        sendMessageToAPI('', { personality: personality });
        toggleSettings();
    }
    
    function updateCurrentPersonalityDisplay() {
        if (currentPersonalityName) {
            currentPersonalityName.textContent = currentPersonality;
        }
        
        if (currentPersonalityEmoji) {
            let emoji = '😊';
            
            switch (currentPersonality) {
                case 'مرح':
                    emoji = '😄';
                    break;
                case 'جدي':
                    emoji = '🧐';
                    break;
                case 'ساخر':
                    emoji = '😏';
                    break;
                case 'حكيم':
                    emoji = '🌟';
                    break;
                case 'عصبي':
                    emoji = '😠';
                    break;
            }
            
            currentPersonalityEmoji.textContent = emoji;
        }
        
        // تحديث العرض المرئي للشخصيات في لوحة الإعدادات
        personalityOptions.forEach(option => {
            option.classList.toggle('active', option.getAttribute('data-personality') === currentPersonality);
        });
    }
    
    function updateContextDisplay(context) {
        contextData = context;
        
        // حفظ المحتوى السابق
        chatContext.innerHTML = '';
        
        // التحقق من وجود سياق لعرضه
        if (!context || Object.keys(context).length === 0) {
            chatContext.classList.add('hidden');
            return;
        }
        
        // إنشاء العناصر لكل عنصر سياق
        for (const [key, value] of Object.entries(context)) {
            if (value) {
                const contextItem = document.createElement('span');
                contextItem.classList.add('context-item');
                contextItem.textContent = `${key}: ${value}`;
                chatContext.appendChild(contextItem);
            }
        }
        
        // عرض قسم السياق إذا كان هناك محتوى
        if (chatContext.childNodes.length > 0) {
            chatContext.classList.remove('hidden');
        } else {
            chatContext.classList.add('hidden');
        }
    }
    
    function addMessage(text, sender, personality = currentPersonality) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        
        // إضافة صنف الشخصية لرسائل البوت
        if (sender === 'bot' && personality) {
            const personalityClass = personalityMapping[personality] || 'fun';
            messageDiv.classList.add(personalityClass);
            
            // إضافة مؤشر الشخصية
            const personalityIndicator = document.createElement('span');
            personalityIndicator.classList.add('personality-indicator', personalityClass);
            personalityIndicator.textContent = personality;
            
            // إضافة المحتوى
            const contentSpan = document.createElement('div');
            contentSpan.textContent = text;
            
            messageDiv.appendChild(personalityIndicator);
            messageDiv.appendChild(contentSpan);
        } else {
            messageDiv.textContent = text;
        }
        
        // إضافة الطابع الزمني
        const timeSpan = document.createElement('span');
        timeSpan.classList.add('message-time');
        const now = new Date();
        timeSpan.textContent = `${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`;
        messageDiv.appendChild(timeSpan);
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
        return messageDiv;
    }
    
    function addSystemMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'system-message');
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
        return messageDiv;
    }
    
    function addTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.classList.add('typing-indicator');
        indicator.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(indicator);
        scrollToBottom();
        return indicator;
    }
    
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // التهيئة المبدئية
    updateCurrentPersonalityDisplay();
});
