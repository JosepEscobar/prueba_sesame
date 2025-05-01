<template>
  <div class="w-full max-w-4xl mx-auto">
    <div class="relative flex items-center">
      <textarea
        ref="textareaRef"
        v-model="inputValue"
        placeholder="Escribe un mensaje..."
        class="input-textarea w-full py-3 px-4 pr-16 rounded-lg resize-none overflow-hidden"
        :rows="rows"
        @keydown.enter.prevent="handleEnter"
        @input="resizeTextarea"
      ></textarea>
      <div class="absolute right-2 flex items-center space-x-1">
        <button 
          @click="$emit('clear')"
          class="clear-button p-2"
          title="Limpiar chat"
        >
          <Trash2 class="w-5 h-5" />
        </button>
        <button 
          @click="sendMessage"
          class="send-button p-2 rounded-lg"
          :disabled="!inputValue.trim()"
          :class="{ 'opacity-50 cursor-not-allowed': !inputValue.trim() }"
        >
          <SendIcon class="w-5 h-5" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { Send as SendIcon, Trash2 } from 'lucide-vue-next';

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['update:modelValue', 'send', 'clear']);

const textareaRef = ref(null);
const rows = ref(1);
const inputValue = ref(props.modelValue);

// Sync con v-model
watch(() => props.modelValue, (newValue) => {
  inputValue.value = newValue;
});

watch(inputValue, (newValue) => {
  emit('update:modelValue', newValue);
});

const sendMessage = () => {
  if (inputValue.value.trim()) {
    emit('send');
    rows.value = 1;
  }
};

const handleEnter = (event) => {
  // Ctrl+Enter para nueva línea, Enter para enviar
  if (!event.shiftKey && !event.ctrlKey) {
    sendMessage();
  }
};

const resizeTextarea = () => {
  const textarea = textareaRef.value;
  if (!textarea) return;
  
  // Resetear altura
  textarea.style.height = 'auto';
  
  // Contar líneas
  const lineCount = Math.min(
    5, // Máximo número de líneas
    Math.ceil(textarea.scrollHeight / 24) // Dividir por altura aprox. de línea
  );
  
  rows.value = lineCount || 1;
  
  // Ajustar altura
  textarea.style.height = `${textarea.scrollHeight}px`;
};

onMounted(() => {
  if (textareaRef.value) {
    textareaRef.value.focus();
  }
});
</script>

<style scoped>
.input-textarea {
  background-color: var(--composer-surface-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-medium);
}

.input-textarea:focus {
  outline: none;
  border-color: transparent;
  box-shadow: 0 0 0 2px var(--border-heavy);
}

.input-textarea::placeholder {
  color: var(--text-placeholder);
}

.clear-button {
  color: var(--text-secondary);
}

.clear-button:hover {
  color: var(--text-primary);
}

.send-button {
  background-color: var(--composer-blue-bg);
  color: var(--text-primary);
}

.send-button:hover {
  background-color: var(--composer-blue-hover);
}
</style> 