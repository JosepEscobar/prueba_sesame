<template>
  <div class="h-full p-6 overflow-y-auto">
    <div class="max-w-4xl mx-auto">
      <h2 class="text-xl font-semibold mb-4">Herramientas MCP</h2>
      
      <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-6 mb-6">
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2">Seleccionar Herramienta</label>
          <select 
            v-model="selectedTool" 
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2"
          >
            <option value="" disabled>Seleccione una herramienta</option>
            <option v-for="tool in tools" :key="tool.name" :value="tool.name">
              {{ tool.name }}
            </option>
          </select>
        </div>
        
        <div v-if="selectedTool && toolParams.length > 0" class="space-y-3 mb-4">
          <h3 class="text-lg font-medium">Parámetros</h3>
          <div v-for="param in toolParams" :key="param.name" class="space-y-1">
            <label class="block text-sm font-medium">{{ param.name }}</label>
            <input 
              v-model="paramValues[param.name]" 
              type="text" 
              class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2"
              :placeholder="param.description || param.name"
            />
            <p v-if="param.description" class="text-xs text-gray-500">{{ param.description }}</p>
          </div>
        </div>
        
        <div class="flex justify-end">
          <button 
            @click="runTool" 
            class="px-4 py-2 bg-primary-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!selectedTool || isLoading"
          >
            <span v-if="isLoading" class="flex items-center">
              <span class="animate-spin mr-2">⟳</span> Ejecutando...
            </span>
            <span v-else>Ejecutar Herramienta</span>
          </button>
        </div>
      </div>
      
      <div v-if="result" class="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
        <h3 class="text-lg font-medium mb-3">Resultado</h3>
        
        <div v-if="error" class="text-red-500 mb-2">{{ error }}</div>
        
        <pre v-else class="bg-gray-100 dark:bg-gray-900 p-4 rounded overflow-x-auto text-sm">{{ formattedResult }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import axios from 'axios';

const tools = ref([]);
const selectedTool = ref('');
const paramValues = ref({});
const result = ref(null);
const error = ref(null);
const isLoading = ref(false);

// Obtener herramientas disponibles al montar
onMounted(async () => {
  try {
    await fetchTools();
  } catch (e) {
    error.value = 'Error al cargar las herramientas: ' + e.message;
  }
});

const fetchTools = async () => {
  try {
    const response = await axios.get('/mcp/status');
    tools.value = response.data?.tools || [];
  } catch (e) {
    console.error('Error fetching tools:', e);
    tools.value = [];
  }
};

// Resetear parámetros cuando cambia la herramienta
watch(selectedTool, () => {
  paramValues.value = {};
  result.value = null;
  error.value = null;
});

// Obtener parámetros de la herramienta seleccionada
const toolParams = computed(() => {
  if (!selectedTool.value) return [];
  
  const tool = tools.value.find(t => t.name === selectedTool.value);
  return tool?.parameters || [];
});

// Ejecutar la herramienta seleccionada
const runTool = async () => {
  if (!selectedTool.value) return;
  
  error.value = null;
  result.value = null;
  isLoading.value = true;
  
  try {
    const response = await axios.post(`/api/v1/tools/${selectedTool.value}`, paramValues.value);
    result.value = response.data;
  } catch (e) {
    console.error('Error running tool:', e);
    error.value = e.response?.data?.message || e.message || 'Error al ejecutar la herramienta';
    result.value = e.response?.data || null;
  } finally {
    isLoading.value = false;
  }
};

// Formatear el resultado para mostrar
const formattedResult = computed(() => {
  if (!result.value) return '';
  
  try {
    if (typeof result.value === 'object') {
      return JSON.stringify(result.value, null, 2);
    }
    return result.value.toString();
  } catch (e) {
    return '[Error al formatear resultado]';
  }
});
</script> 