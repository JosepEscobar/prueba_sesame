<template>
  <div class="h-full p-6 overflow-y-auto">
    <div class="max-w-4xl mx-auto">
      <h2 class="text-xl font-semibold mb-4">Análisis Financiero</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div 
          class="bg-white dark:bg-gray-800 shadow rounded-lg p-4 hover:shadow-md transition cursor-pointer"
          @click="activeTab = 'analyze'"
          :class="{ 'ring-2 ring-primary-500': activeTab === 'analyze' }"
        >
          <div class="flex items-center mb-2">
            <BarChart2 class="w-5 h-5 text-primary-600 mr-2" />
            <h3 class="font-medium">Análisis</h3>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Analiza datos financieros históricos y obtén insights.
          </p>
        </div>
        
        <div 
          class="bg-white dark:bg-gray-800 shadow rounded-lg p-4 hover:shadow-md transition cursor-pointer"
          @click="activeTab = 'forecast'"
          :class="{ 'ring-2 ring-primary-500': activeTab === 'forecast' }"
        >
          <div class="flex items-center mb-2">
            <TrendingUp class="w-5 h-5 text-primary-600 mr-2" />
            <h3 class="font-medium">Pronóstico</h3>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Genera pronósticos financieros basados en datos históricos.
          </p>
        </div>
      </div>
      
      <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h3 class="text-lg font-medium mb-4">
          {{ activeTab === 'analyze' ? 'Análisis Financiero' : 'Pronóstico Financiero' }}
        </h3>
        
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2">Consulta</label>
          <textarea
            v-model="query"
            rows="3"
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2"
            :placeholder="activeTab === 'analyze' 
              ? 'Ej: Analiza el rendimiento financiero del último trimestre' 
              : 'Ej: Genera un pronóstico de ingresos para los próximos 3 meses'"
          ></textarea>
        </div>
        
        <div class="flex justify-end mb-6">
          <button 
            @click="submitQuery" 
            class="px-4 py-2 bg-primary-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
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
          
          <div v-else-if="resultData.table" class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-300 dark:divide-gray-700">
              <thead>
                <tr>
                  <th v-for="(header, i) in resultData.table.headers" :key="i" 
                      class="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
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
          
          <div v-if="resultData.text" class="mt-4 text-gray-800 dark:text-gray-200">
            {{ resultData.text }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import axios from 'axios';
import { BarChart2, TrendingUp } from 'lucide-vue-next';

const activeTab = ref('analyze'); // 'analyze' o 'forecast'
const query = ref('');
const result = ref(null);
const error = ref(null);
const isLoading = ref(false);

const submitQuery = async () => {
  if (!query.value.trim()) return;
  
  error.value = null;
  result.value = null;
  isLoading.value = true;
  
  const endpoint = activeTab.value === 'analyze' 
    ? '/api/v1/finance/analyze'
    : '/api/v1/finance/forecast';
  
  try {
    const response = await axios.post(endpoint, {
      query: query.value
    });
    
    result.value = response.data;
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
</script> 