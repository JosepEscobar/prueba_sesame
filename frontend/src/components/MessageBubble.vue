<template>
  <div :class="bubbleClass">
    <div v-if="message.isLoading" class="flex items-center space-x-1">
      <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
      <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
      <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
    </div>
    <div v-else-if="message.isError" class="text-red-500">
      {{ message.content }}
    </div>
    <div v-else-if="isDataObject" class="space-y-2">
      <div v-if="messageData.title" class="font-medium mb-1">{{ messageData.title }}</div>
      
      <table v-if="messageData.table" class="min-w-full divide-y divide-gray-300 dark:divide-gray-700">
        <thead>
          <tr>
            <th v-for="(header, i) in messageData.table.headers" :key="i" 
                class="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ header }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-gray-800">
          <tr v-for="(row, rowIndex) in messageData.table.rows" :key="rowIndex">
            <td v-for="(cell, cellIndex) in row" :key="cellIndex" 
                class="px-3 py-2 whitespace-nowrap text-sm">
              {{ cell }}
            </td>
          </tr>
        </tbody>
      </table>
      
      <p v-if="messageData.text">{{ messageData.text }}</p>
      
      <div v-if="messageData.items" class="space-y-1">
        <div v-for="(item, index) in messageData.items" :key="index" 
             class="flex items-start">
          <span class="mr-2">•</span>
          <span>{{ item }}</span>
        </div>
      </div>
    </div>
    <div v-else class="whitespace-pre-wrap break-words">{{ message.content }}</div>
    <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
      {{ formatTime(message.timestamp) }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  isUser: {
    type: Boolean,
    default: false
  }
});

const bubbleClass = computed(() => {
  return props.isUser
    ? 'user-bubble'
    : 'api-bubble';
});

const isDataObject = computed(() => {
  if (typeof props.message.content === 'object') return true;
  
  try {
    // Intenta analizar como JSON si es un string
    if (typeof props.message.content === 'string') {
      const parsed = JSON.parse(props.message.content);
      return typeof parsed === 'object' && parsed !== null;
    }
  } catch (e) {
    return false;
  }
  
  return false;
});

const messageData = computed(() => {
  if (isDataObject.value) {
    if (typeof props.message.content === 'object') {
      return props.message.content;
    }
    try {
      return JSON.parse(props.message.content);
    } catch (e) {
      return {};
    }
  }
  return {};
});

const formatTime = (timestamp) => {
  if (!timestamp) return '';
  
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};
</script> 