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
    <div v-else>
      <!-- Si es mensaje del usuario, lo mostramos como texto plano -->
      <div v-if="isUser" class="whitespace-pre-wrap break-words">{{ message.content }}</div>
      <!-- Para los mensajes del sistema, renderizar Markdown -->
      <div v-else>
        <div class="markdown-body" v-html="renderedMarkdown"></div>
      </div>
    </div>
    <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
      {{ formatTime(message.timestamp) }}
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import 'highlight.js/styles/github-dark.css';

let md;
onMounted(() => {
  // Inicializar markdown-it con opciones de GitHub style
  md = new MarkdownIt({
    html: false,        // No permitir HTML en la entrada
    xhtmlOut: false,    // No usar XHTML
    breaks: true,       // Convertir \n en <br>
    linkify: true,      // Autoconvertir URLs en enlaces
    typographer: true,  // Sustituir (c) (tm) etc.
    highlight: function (str, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return '<pre class="hljs"><code>' +
                 hljs.highlight(str, { language: lang, ignoreIllegals: true }).value +
                 '</code></pre>';
        } catch (__) {}
      }
      
      return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>';
    }
  });
});

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

// Renderizar Markdown
const renderedMarkdown = computed(() => {
  if (!md || !props.message.content) {
    return '';
  }
  
  try {
    return md.render(props.message.content);
  } catch (e) {
    console.error('Error al renderizar Markdown:', e);
    return `<div class="text-red-500">Error al renderizar: ${e.message}</div>
            <div class="whitespace-pre-wrap">${props.message.content}</div>`;
  }
});

const formatTime = (timestamp) => {
  if (!timestamp) return '';
  
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};
</script>

<style>
/* Estilos básicos para los mensajes */
.user-bubble {
  background-color: var(--message-surface);
  color: var(--text-primary);
  border-radius: 0.75rem;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  align-self: flex-end;
  max-width: 80%;
  margin-left: auto;
}

.api-bubble {
  background-color: transparent;
  color: var(--text-primary);
  border-radius: 0.75rem;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  align-self: flex-start;
  max-width: 80%;
  margin-right: auto;
}

/* Estilos para Markdown GitHub style */
.markdown-body {
  color: var(--text-primary);
  font-size: 16px;
  line-height: 1.5;
}

.markdown-body a {
  color: var(--link);
  text-decoration: underline;
}

.markdown-body a:hover {
  text-decoration: underline;
  color: var(--link-hover);
}

.markdown-body strong {
  font-weight: 600;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body h1 {
  font-size: 2em;
  margin-bottom: 0.5em;
}

.markdown-body h2 {
  font-size: 1.5em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid var(--border-light);
}

.markdown-body h3 {
  font-size: 1.25em;
}

.markdown-body h4 {
  font-size: 1em;
}

.markdown-body code {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: var(--composer-surface-primary);
  border-radius: 3px;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}

.markdown-body pre {
  margin-top: 0.5em;
  margin-bottom: 1em;
  padding: 16px;
  overflow: auto;
  background-color: var(--composer-surface-primary);
  border-radius: 3px;
}

.markdown-body pre code {
  padding: 0;
  margin: 0;
  font-size: 0.9em;
  word-break: normal;
  white-space: pre;
  background: transparent;
  border: 0;
  display: inline;
}

.markdown-body ul,
.markdown-body ol {
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 1em;
}

.markdown-body ul {
  list-style-type: disc;
}

.markdown-body ol {
  list-style-type: decimal;
}

.markdown-body li {
  margin-bottom: 0.25em;
}

.markdown-body li + li {
  margin-top: 0.25em;
}

.markdown-body blockquote {
  margin: 1em 0;
  padding: 0 1em;
  color: var(--text-secondary);
  border-left: 0.25em solid var(--border-medium);
}

.markdown-body img {
  max-width: 100%;
  box-sizing: content-box;
  background-color: var(--main-surface-background);
}

.markdown-body hr {
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: var(--border-light);
  border: 0;
}

.markdown-body table {
  display: block;
  width: 100%;
  overflow: auto;
  margin-top: 0;
  margin-bottom: 16px;
  border-spacing: 0;
  border-collapse: collapse;
}

.markdown-body table tr {
  background-color: transparent;
  border-top: 1px solid var(--border-light);
}

.markdown-body table tr:nth-child(2n) {
  background-color: var(--surface-hover);
}

.markdown-body table th,
.markdown-body table td {
  padding: 6px 13px;
  border: 1px solid var(--border-medium);
}

.markdown-body table th {
  font-weight: 600;
}
</style> 