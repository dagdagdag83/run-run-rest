<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { marked } from 'marked';

const isAuthenticated = ref(false);
const userFirstName = ref('Athlete');
const chatInput = ref('');
const isSubmitting = ref(false);
const chatLogRef = ref(null);

const messages = ref([]);

const scrollToBottom = () => {
    nextTick(() => {
        if (chatLogRef.value) {
            const lastChild = chatLogRef.value.lastElementChild;
            if (lastChild) {
                lastChild.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }
        }
    });
};

const checkAuth = async () => {
    try {
        const response = await fetch('/api/me');
        if (response.status === 200) {
            const data = await response.json();
            isAuthenticated.value = true;
            userFirstName.value = data.user.given_name || (data.user.name ? data.user.name.split(' ')[0] : null) || data.user.preferred_username || 'Athlete';
            
            try {
                const historyResp = await fetch('/chat/history');
                if (historyResp.ok) {
                    const historyData = await historyResp.json();
                    if (historyData.messages && historyData.messages.length > 0) {
                        messages.value = historyData.messages;
                        scrollToBottom();
                    }
                }
            } catch (e) {
                console.error('Failed to load chat history:', e);
            }
        }
    } catch (error) {
        console.error("Auth check failed:", error);
    }
};

const formatMessage = (msg) => {
    let displayTime = '';
    let contentText = msg.content;
    
    const timeMatch = contentText.match(/^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\s*/);
    if (timeMatch) {
        const utcDateStr = timeMatch[1].replace(' ', 'T') + ':00Z';
        const dateObj = new Date(utcDateStr);
        if (!isNaN(dateObj)) {
            const today = new Date();
            const isToday = dateObj.getDate() === today.getDate() &&
                dateObj.getMonth() === today.getMonth() &&
                dateObj.getFullYear() === today.getFullYear();
                
            if (isToday) {
                displayTime = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            } else {
                displayTime = dateObj.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ', ' + dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            }
            contentText = contentText.substring(timeMatch[0].length);
        }
    }
    return { displayTime, contentText };
};

const renderMarkdown = (text) => {
    return marked.parse(text);
};

const sendMessage = async () => {
    const text = chatInput.value.trim();
    if (!text) return;

    chatInput.value = '';
    isSubmitting.value = true;
    
    const localDisplayTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const optimisticMessage = {
        role: 'user',
        content: text,
        _localTime: localDisplayTime
    };
    messages.value.push(optimisticMessage);
    scrollToBottom();
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: text })
        });

        if (response.ok) {
            const data = await response.json();
            if (data.messages) {
                messages.value = data.messages;
                scrollToBottom();
            }
        } else if (response.status === 401) {
            window.location.reload(); 
        } else {
            console.error("Failed to send message:", await response.text());
            messages.value.pop(); // remove optimistic msg on fail
        }
    } catch (error) {
        console.error("Error sending message:", error);
        messages.value.pop();
    } finally {
        isSubmitting.value = false;
        nextTick(() => {
            const inputEl = document.getElementById('chat-input');
            if (inputEl) inputEl.focus();
        });
    }
};

const handleKeydown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
};

onMounted(() => {
    document.body.classList.add('bg-run-run-rest-base', 'text-slate-50', 'font-sans');
    checkAuth();
});
</script>

<template>
  <div class="h-screen w-full flex flex-col items-center justify-center p-0 sm:p-4">
    <div class="w-full max-w-7xl h-full max-h-[95vh] bg-run-run-rest-surface flex flex-col sm:rounded-2xl shadow-2xl overflow-hidden border border-white/10">
      
      <!-- Header -->
      <div class="p-6 border-b border-white/10 bg-run-run-rest-surface/50 backdrop-blur-sm flex justify-between items-center gap-4">
          <div class="flex items-center gap-4">
              <img src="/run-run-rest-logo.png" alt="Run-Run-Rest Logo" class="h-10 sm:h-12 w-auto object-contain hidden sm:block" />
              <img src="/run-run-rest-logo-small.png" alt="Run-Run-Rest Logo" class="h-10 w-auto object-contain sm:hidden" />
              <div>
                  <h1 class="text-2xl font-bold text-run-run-rest-accent">Run-Run-Rest</h1>
                  <p class="text-run-run-rest-muted text-sm mt-1">Agentic Fitness Harness</p>
              </div>
          </div>
          <div id="auth-section" class="text-sm">
            <div v-if="isAuthenticated" class="flex flex-col items-end">
                <span class="text-slate-300 font-medium">Hi, {{ userFirstName }}</span>
                <a href="/logout" class="text-run-run-rest-primary hover:text-run-run-rest-primary/80 text-xs mt-1 transition-colors">Logout</a>
            </div>
          </div>
      </div>

      <!-- Login Overlay -->
      <div v-if="!isAuthenticated" id="login-overlay" class="flex-1 flex flex-col items-center justify-center p-6 text-center">
          <h2 class="text-xl text-slate-200 mb-4 font-semibold">Welcome to your Coach</h2>
          <p class="text-run-run-rest-muted mb-8 max-w-sm">Please log in with Zitadel to synchronize your fitness profile and access the agentic harness.</p>
          <a href="/login" class="bg-run-run-rest-primary hover:bg-run-run-rest-primary/90 text-white rounded-lg px-6 py-3 font-medium transition-colors shadow-lg shadow-run-run-rest-primary/20 active:scale-95">
              Login with Zitadel
          </a>
      </div>

      <!-- Authenticated Content -->
      <div v-else id="app-content" class="flex-1 flex col flex-col overflow-hidden">
          <!-- Chat Log Area -->
          <div id="chat-log" ref="chatLogRef" class="flex-1 overflow-y-auto p-6 space-y-4">
              <div v-for="(msg, index) in messages" :key="index" class="flex flex-col max-w-[90%]" :class="msg.role === 'user' ? 'ml-auto items-end' : 'items-start'">
                <!-- Time -->
                <span v-if="msg._localTime" class="text-[10px] text-run-run-rest-muted mb-1 px-1">{{ msg._localTime }}</span>
                <span v-else-if="formatMessage(msg).displayTime" class="text-[10px] text-run-run-rest-muted mb-1 px-1">{{ formatMessage(msg).displayTime }}</span>
                
                <!-- Bubble -->
                <div v-if="msg.role === 'user'" class="bg-run-run-rest-base text-slate-100 rounded-2xl rounded-tr-none px-4 py-3 text-sm leading-[1.8]">
                    {{ formatMessage(msg).contentText }}
                </div>
                <div v-else class="bg-run-run-rest-primary/20 border border-run-run-rest-primary/30 text-slate-100 rounded-2xl rounded-tl-none px-6 py-4 text-sm prose prose-invert prose-sm max-w-none prose-p:leading-[1.8] prose-li:leading-[1.8]" v-html="renderMarkdown(formatMessage(msg).contentText)"></div>
              </div>

              <!-- Waiting indicator -->
              <div v-if="isSubmitting" id="thinking-bubble" class="flex items-start max-w-[90%] mt-4">
                  <div class="bg-run-run-rest-primary/20 border border-run-run-rest-primary/30 text-indigo-100 rounded-2xl rounded-tl-none px-4 py-3 text-sm flex items-center gap-2">
                      <div class="w-2 h-2 bg-run-run-rest-primary rounded-full animate-bounce" style="animation-delay: 0s"></div>
                      <div class="w-2 h-2 bg-run-run-rest-primary rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                      <div class="w-2 h-2 bg-run-run-rest-primary rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
                  </div>
              </div>
          </div>

          <!-- Input Area -->
          <div class="p-4 bg-run-run-rest-surface border-t border-white/10">
              <div class="flex items-end gap-3 rounded-xl bg-run-run-rest-base/50 p-2 border border-white/10 focus-within:border-run-run-rest-primary/50 focus-within:ring-1 focus-within:ring-run-run-rest-primary/50 transition-all">
                  <textarea 
                      id="chat-input"
                      v-model="chatInput"
                      @keydown="handleKeydown"
                      class="w-full bg-transparent text-slate-200 px-3 py-2 outline-none resize-none placeholder:text-run-run-rest-muted text-sm max-h-32 min-h-[44px]"
                      placeholder="Type your message..."
                      rows="1"
                  ></textarea>
                  <button 
                      id="submit-btn" 
                      @click="sendMessage"
                      :disabled="isSubmitting || !chatInput.trim()"
                      class="bg-run-run-rest-primary hover:bg-run-run-rest-primary/90 text-white rounded-lg px-4 py-2.5 text-sm font-medium transition-colors shadow-lg shadow-run-run-rest-primary/20 active:scale-95 disabled:opacity-50 flex-shrink-0"
                  >
                      Send
                  </button>
              </div>
          </div>
      </div>
      
    </div>
  </div>
</template>

<style>
/* Any custom overrides or imported typography plugin styles would go here */
body {
    background-color: #0C0F0A; /* fallback */
}

/* Force airy line height on chat bubbles */
.prose p, .prose li {
    line-height: 1.8 !important;
}
</style>
