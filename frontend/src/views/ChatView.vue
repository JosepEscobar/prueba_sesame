<template>
  <div class="h-full flex flex-col">
    <div class="flex-1 overflow-y-auto p-4" ref="chatContainer">
      <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center">
        <div class="text-center mb-8">
          <h2 class="text-2xl font-semibold mb-2">Bienvenido a Sesame Chat</h2>
          <p class="text-gray-600 dark:text-gray-400">¿Qué te gustaría hacer hoy?</p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl">
          <SuggestionBubbles @select="sendSuggestion" />
        </div>
      </div>
      <div v-else class="space-y-4 pb-4">
        <MessageBubble
          v-for="(message, index) in messages"
          :key="index"
          :message="message"
          :is-user="message.isUser"
        />
      </div>
    </div>
    <div class="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4">
      <ChatInput 
        v-model="userInput" 
        @send="sendMessage" 
        @clear="clearChat" 
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import axios from 'axios';
import MessageBubble from '../components/MessageBubble.vue';
import ChatInput from '../components/ChatInput.vue';
import SuggestionBubbles from '../components/SuggestionBubbles.vue';

const messages = ref([]);
const userInput = ref('');
const chatContainer = ref(null);

const sendMessage = async () => {
  if (!userInput.value.trim()) return;
  
  // Añadir mensaje del usuario
  const userMessage = {
    content: userInput.value,
    isUser: true,
    timestamp: new Date()
  };
  
  messages.value.push(userMessage);
  const tempInput = userInput.value;
  userInput.value = '';
  
  // Scroll al final
  await nextTick();
  scrollToBottom();
  
  try {
    // Añadir mensaje temporal de "escribiendo..."
    const loadingMessage = {
      content: 'Procesando respuesta...',
      isUser: false,
      isLoading: true,
      timestamp: new Date()
    };
    messages.value.push(loadingMessage);
    
    // Llamar a la API
    const response = await axios.post('/api/v1/query', {
      prompt: tempInput
    });
    
    // Reemplazar mensaje de carga con respuesta
    const apiResponseIndex = messages.value.findIndex(msg => msg.isLoading);
    if (apiResponseIndex !== -1) {
      messages.value[apiResponseIndex] = {
        content: response.data,
        isUser: false,
        timestamp: new Date()
      };
    }
  } catch (error) {
    // Mostrar error
    const errorIndex = messages.value.findIndex(msg => msg.isLoading);
    if (errorIndex !== -1) {
      messages.value[errorIndex] = {
        content: `Error: ${error.response?.data?.message || 'No se pudo obtener una respuesta'}`,
        isUser: false,
        isError: true,
        timestamp: new Date()
      };
    }
    console.error('Error al enviar mensaje:', error);
  }
  
  // Scroll al final nuevamente
  await nextTick();
  scrollToBottom();
};

const sendSuggestion = (suggestion) => {
  userInput.value = suggestion;
  sendMessage();
};

const clearChat = () => {
  messages.value = [];
};

const scrollToBottom = () => {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

// Scroll cuando cambia el número de mensajes
watch(() => messages.value.length, () => {
  nextTick(scrollToBottom);
});

// Obtener mensaje de bienvenida al cargar
const fetchWelcomeMessage = async () => {
  try {
    const response = await axios.get('/');
    if (response.data) {
      messages.value.push({
        content: response.data,
        isUser: false,
        timestamp: new Date()
      });
    }
  } catch (error) {
    console.error('Error al cargar mensaje de bienvenida:', error);
  }
};

// Si quieres mostrar mensaje de bienvenida automáticamente, descomenta esta línea:
// fetchWelcomeMessage();
</script> 