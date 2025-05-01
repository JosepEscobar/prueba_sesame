<template>
  <div class="h-full flex flex-col">
    <div class="flex-1 overflow-y-auto p-4" ref="chatContainer">
      <div class="max-w-4xl mx-auto">
        <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center">
          <div class="text-center mb-10">
            <h2 class="text-3xl font-semibold mb-3">Bienvenido a Sesame Chat</h2>
            <p class="text-gray-600 dark:text-gray-400 text-lg">¿Qué te gustaría hacer hoy?</p>
          </div>
          <div class="w-full px-4">
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
    </div>
    <div class="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4">
      <div class="max-w-4xl mx-auto">
        <ChatInput 
          v-model="userInput" 
          @send="sendMessage" 
          @clear="clearChat" 
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue';
import axios from 'axios';
import MessageBubble from '../components/MessageBubble.vue';
import ChatInput from '../components/ChatInput.vue';
import SuggestionBubbles from '../components/SuggestionBubbles.vue';

const messages = ref([]);
const userInput = ref('');
const chatContainer = ref(null);

// NO cargar mensaje de bienvenida automáticamente para permitir que se muestren las tarjetas
// onMounted(() => {
//   fetchWelcomeMessage();
// });

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
      query: tempInput,
      context: {
        previous_messages: messages.value
          .filter(msg => !msg.isLoading)
          .map(msg => ({
            role: msg.isUser ? 'user' : 'assistant',
            content: msg.content
          }))
      }
    });
    
    // Reemplazar mensaje de carga con respuesta
    const apiResponseIndex = messages.value.findIndex(msg => msg.isLoading);
    if (apiResponseIndex !== -1) {
      messages.value[apiResponseIndex] = {
        content: response.data.result && typeof response.data.result === 'object' ? 
                 response.data.result.content || JSON.stringify(response.data.result) : 
                 response.data.result || response.data,
        agent: response.data.agent,
        confidence: response.data.confidence,
        isUser: false,
        timestamp: new Date()
      };
    }
  } catch (error) {
    // Mostrar error
    const errorIndex = messages.value.findIndex(msg => msg.isLoading);
    if (errorIndex !== -1) {
      let errorMessage = 'No se pudo conectar con el backend';
      
      if (error.response) {
        // El servidor respondió con un código de error
        const statusCode = error.response.status;
        const data = error.response.data;
        
        if (statusCode === 422) {
          errorMessage = 'Error 422: Formato de consulta inválido. Revise la estructura de datos enviada.';
          console.error('Datos enviados:', { query: tempInput });
          console.error('Respuesta del servidor:', data);
        } else {
          errorMessage = `Error ${statusCode}: ${data.detail || data.message || JSON.stringify(data)}`;
        }
      } else if (error.request) {
        // La solicitud se realizó pero no se recibió respuesta
        errorMessage = 'No se recibió respuesta del servidor. Verifique que el backend esté funcionando en localhost:8000.';
      } else {
        // Error al configurar la solicitud
        errorMessage = `Error al configurar la solicitud: ${error.message}`;
      }
      
      messages.value[errorIndex] = {
        content: `Error: ${errorMessage}`,
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
    console.log("Obteniendo mensaje de bienvenida desde: http://localhost:8000/");
    const response = await axios.get('/');
    console.log("Respuesta recibida:", response.data);
    if (response.data) {
      messages.value.push({
        content: response.data,
        isUser: false,
        timestamp: new Date()
      });
    }
  } catch (error) {
    console.error('Error al cargar mensaje de bienvenida:', error);
    messages.value.push({
      content: "Bienvenido a Sesame Chat. Asegúrate de que el backend esté funcionando en localhost:8000.",
      isUser: false,
      isError: true,
      timestamp: new Date()
    });
  }
};
</script> 