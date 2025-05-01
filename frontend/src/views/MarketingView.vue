<template>
  <div class="h-full p-6 overflow-y-auto">
    <div class="max-w-4xl mx-auto">
      <h2 class="text-xl font-semibold mb-4">Marketing</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div 
          style="background-color: var(--message-surface);"
          class="shadow rounded-lg p-4 hover:shadow-md transition cursor-pointer"
          @click="activeTab = 'analyze'"
          :class="{ 'ring-2 ring-primary-500': activeTab === 'analyze' }"
        >
          <div class="flex items-center mb-2">
            <BarChart class="w-5 h-5 text-gray-300 mr-2" />
            <h3 class="font-medium">Análisis</h3>
          </div>
          <p class="text-sm text-gray-400">
            Analiza el rendimiento de campañas de marketing existentes.
          </p>
        </div>
        
        <div 
          style="background-color: var(--message-surface);"
          class="shadow rounded-lg p-4 hover:shadow-md transition cursor-pointer"
          @click="activeTab = 'campaign'"
          :class="{ 'ring-2 ring-primary-500': activeTab === 'campaign' }"
        >
          <div class="flex items-center mb-2">
            <Megaphone class="w-5 h-5 text-gray-300 mr-2" />
            <h3 class="font-medium">Campañas</h3>
          </div>
          <p class="text-sm text-gray-400">
            Desarrolla nuevas estrategias y campañas de marketing.
          </p>
        </div>
      </div>
      
      <div style="background-color: var(--message-surface);" class="shadow rounded-lg p-6">
        <h3 class="text-lg font-medium mb-4">
          {{ activeTab === 'analyze' ? 'Análisis de Marketing' : 'Generación de Campañas' }}
        </h3>
        
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2">Consulta</label>
          <textarea
            v-model="query"
            rows="3"
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600" 
            style="background-color: #292929; padding: 1em;"
            :placeholder="activeTab === 'analyze' 
              ? 'Ej: Analiza el rendimiento de nuestra última campaña en redes sociales' 
              : 'Ej: Diseña una campaña para aumentar la conversión de visitantes a clientes'"
          ></textarea>
        </div>
        
        <div class="flex justify-end mb-6">
          <button 
            @click="submitQuery" 
            class="px-4 py-2 bg-gray-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!query.trim() || isLoading"
          >
            <span v-if="isLoading" class="flex items-center">
              <span class="animate-spin mr-2">⟳</span> Procesando...
            </span>
            <span v-else>Procesar Consulta</span>
          </button>
        </div>
        
        <div v-if="result" class="mt-4">
          <h4 class="font-medium mb-2">Resultado</h4>
          
          <div v-if="error" class="text-red-500 mb-2">{{ error }}</div>
          
          <div v-else>
            <!-- Métricas clave en tarjetas (si existen) -->
            <div v-if="resultData.metrics && resultData.metrics.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
              <div 
                v-for="(metric, index) in resultData.metrics" 
                :key="index"
                style="background-color: #292929;"
                class="p-4 rounded-lg text-center"
              >
                <div class="text-gray-400 text-sm mb-1">{{ metric.name }}</div>
                <div class="font-bold text-xl">{{ metric.value }}</div>
                <div 
                  v-if="metric.change" 
                  :class="metric.change > 0 ? 'text-green-500' : 'text-red-500'"
                  class="text-sm"
                >
                  {{ metric.change > 0 ? '↑' : '↓' }} {{ Math.abs(metric.change) }}%
                </div>
              </div>
            </div>
            
            <!-- Tabla de datos (si existe) -->
            <div v-if="resultData.table" class="overflow-x-auto mb-4">
              <table class="min-w-full divide-y divide-gray-300 dark:divide-gray-700">
                <thead>
                  <tr>
                    <th v-for="(header, i) in resultData.table.headers" :key="i" 
                        class="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      {{ header }}
                    </th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-800">
                  <tr v-for="(row, rowIndex) in resultData.table.rows" :key="rowIndex">
                    <td v-for="(cell, cellIndex) in row" :key="cellIndex" 
                        class="px-3 py-2 whitespace-nowrap text-sm">
                      {{ cell }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <!-- Texto o descripción (si existe) -->
            <div v-if="resultData.text" class="text-gray-200 whitespace-pre-line">
              {{ resultData.text }}
            </div>
            
            <!-- Lista de elementos (si existe) -->
            <div v-if="resultData.items && resultData.items.length" class="mt-4">
              <ul class="list-disc list-inside space-y-2">
                <li v-for="(item, index) in resultData.items" :key="index" class="text-gray-800 dark:text-gray-200">
                  {{ item }}
                </li>
              </ul>
            </div>
            
            <!-- Renderizado de Markdown para cuando no hay ningún formato reconocido -->
            <div v-if="!resultData.metrics && !resultData.table && !resultData.text && !resultData.items" 
                 class="markdown-body" v-html="renderedMarkdown">
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { BarChart, Megaphone } from 'lucide-vue-next';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import 'highlight.js/styles/github-dark.css';

// Inicializar markdown-it
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

const activeTab = ref('analyze'); // 'analyze' o 'campaign'
const query = ref('');
const result = ref(null);
const error = ref(null);
const isLoading = ref(false);

const submitQuery = async () => {
  if (!query.value.trim()) return;
  
  error.value = null;
  result.value = null;
  isLoading.value = true;
  
  // Endpoint que vamos a utilizar
  const endpoint = '/api/v1/query';
  console.log('Enviando consulta a endpoint:', endpoint);
  
  try {
    const requestData = {
      query: query.value,
      context: {},
      agent_preference: 'marketing'
    };
    console.log('Datos de la solicitud:', requestData);
    
    const response = await axios.post(endpoint, requestData);
    console.log('Respuesta recibida:', response.data);
    
    // Verificar estructura de la respuesta
    if (response.data && response.data.result) {
      console.log('Estructura del resultado:', {
        type: typeof response.data.result,
        isNull: response.data.result === null,
        isEmpty: response.data.result === '',
        keys: typeof response.data.result === 'object' ? Object.keys(response.data.result) : 'N/A'
      });
      
      result.value = response.data.result;
      console.log('result.value asignado:', result.value);
    } else {
      console.warn('Respuesta sin estructura esperada:', response.data);
      // Intentar usar el objeto completo como resultado
      result.value = response.data;
    }
  } catch (e) {
    console.error(`Error en ${activeTab.value}:`, e);
    error.value = e.response?.data?.message || e.message || 'Error al procesar la consulta';
  } finally {
    isLoading.value = false;
  }
};

const resultData = computed(() => {
  if (!result.value) return {};
  
  try {
    if (typeof result.value === 'string') {
      try {
        return JSON.parse(result.value);
      } catch (e) {
        return { text: result.value };
      }
    }
    
    return result.value;
  } catch (e) {
    return { text: 'Error al formatear el resultado' };
  }
});

const formatResult = () => {
  console.log('Formateando resultado:', result.value);
  if (!result.value) return 'No hay resultado disponible';
  
  if (typeof result.value === 'string') return result.value;
  
  try {
    return JSON.stringify(result.value, null, 2);
  } catch (e) {
    return String(result.value);
  }
};

// Renderizar Markdown del contenido
const renderedMarkdown = computed(() => {
  if (!md || !result.value) {
    return '';
  }
  
  try {
    // Si el resultado contiene 'content', usar ese campo para markdown
    const content = getResultContent();
    if (!content) return '';
    
    return md.render(content);
  } catch (e) {
    console.error('Error al renderizar Markdown:', e);
    return `<div class="text-red-500">Error al renderizar: ${e.message}</div>
            <div class="whitespace-pre-wrap">${getResultContent()}</div>`;
  }
});

// Obtener el contenido del resultado
const getResultContent = () => {
  if (!result.value) return '';
  
  // Si es un objeto y tiene un campo content, usar ese
  if (typeof result.value === 'object' && result.value !== null) {
    if (result.value.content) return result.value.content;
    
    // Intentar otras propiedades comunes donde podría estar el contenido
    if (result.value.text) return result.value.text;
  }
  
  // Si es string, devolver directamente
  if (typeof result.value === 'string') return result.value;
  
  // Último recurso: convertir a JSON
  try {
    return JSON.stringify(result.value, null, 2);
  } catch (e) {
    return String(result.value);
  }
};
</script>

<style>
/* Estilos para Markdown GitHub style */
.markdown-body {
  color: var(--text-primary);
  font-size: 16px;
  line-height: 1.5;
}

.markdown-body a {
  color: #58a6ff;
  text-decoration: underline;
}

.markdown-body a:hover {
  text-decoration: underline;
  color: #79c0ff;
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
  border-bottom: 1px solid #30363d;
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
  background-color: #2d333b;
  border-radius: 3px;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}

.markdown-body pre {
  margin-top: 0.5em;
  margin-bottom: 1em;
  padding: 16px;
  overflow: auto;
  background-color: #2d333b;
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
  color: #8b949e;
  border-left: 0.25em solid #30363d;
}

.markdown-body img {
  max-width: 100%;
  box-sizing: content-box;
  background-color: #0d1117;
}

.markdown-body hr {
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: #30363d;
  border: 0;
}
</style> 