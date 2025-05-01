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
            
            <!-- Fallback para cuando no hay ningún formato reconocido -->
            <div v-if="!resultData.metrics && !resultData.table && !resultData.text && !resultData.items" class="mt-4 p-4 rounded-lg" style="background-color: #292929;">
              <pre class="text-gray-200 whitespace-pre-wrap overflow-x-auto">{{ formatResult() }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import axios from 'axios';
import { BarChart, Megaphone } from 'lucide-vue-next';

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
</script> 