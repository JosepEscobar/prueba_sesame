<template>
  <div class="h-full p-6 overflow-y-auto">
    <div class="max-w-4xl mx-auto">
      <h2 class="text-xl font-semibold mb-4">Herramientas MCP</h2>
      
      <div style="background-color: var(--message-surface);" class="shadow rounded-lg p-6 mb-6">
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2">Seleccionar Herramienta</label>
          <div v-if="tools.length === 0" class="text-yellow-500 mb-2 text-sm">
            Cargando herramientas o no hay herramientas disponibles...
          </div>
          <select 
            v-model="selectedTool" 
            class="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white" 
            style="background-color: #292929; padding: 0.5em;"
          >
            <option value="" disabled>Seleccione una herramienta</option>
            <option v-for="tool in tools" :key="tool.name" :value="tool.name">
              {{ tool.name }}
            </option>
          </select>
        </div>
        
        <div v-if="selectedTool" class="space-y-3 mb-4">
          <h3 class="text-lg font-medium">{{ getSelectedToolName() }}</h3>
          
          <div v-if="getSelectedToolDescription()" class="text-gray-400 text-sm mb-4">
            {{ getSelectedToolDescription() }}
          </div>

          <div v-if="toolParams.length > 0">
            <h4 class="font-medium mb-2">Parámetros</h4>
            <div v-for="param in toolParams" :key="param.name" class="space-y-1">
              <label class="block text-sm font-medium">{{ param.name }}</label>
              <input 
                v-model="paramValues[param.name]" 
                type="text" 
                class="w-full rounded-lg border border-gray-300 dark:border-gray-600" 
                style="background-color: #292929; padding: 0.5em;"
                :placeholder="param.description || param.name"
              />
              <p v-if="param.description" class="text-xs text-gray-500">{{ param.description }}</p>
            </div>
          </div>

          <div v-else class="text-sm text-gray-400">
            Esta herramienta no tiene parámetros o no se pudieron cargar.
          </div>
        </div>
        
        <div class="flex justify-end">
          <button 
            @click="runTool" 
            class="px-4 py-2 bg-gray-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="!selectedTool || isLoading"
          >
            <span v-if="isLoading" class="flex items-center">
              <span class="animate-spin mr-2">⟳</span> Ejecutando...
            </span>
            <span v-else>Ejecutar Herramienta</span>
          </button>
        </div>
      </div>
      
      <div v-if="result" style="background-color: var(--message-surface);" class="shadow rounded-lg p-6">
        <h3 class="text-lg font-medium mb-3">Resultado</h3>
        
        <div v-if="error" class="text-red-500 mb-2">{{ error }}</div>
        
        <pre v-else style="background-color: #292929;" class="p-4 rounded overflow-x-auto text-sm">{{ formattedResult }}</pre>
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
  console.log('Componente ToolsView montado, obteniendo herramientas...');
  try {
    await fetchTools();
  } catch (e) {
    console.error('Error al cargar las herramientas:', e);
    error.value = 'Error al cargar las herramientas: ' + e.message;
  }
});

const fetchTools = async () => {
  console.log('Iniciando fetchTools...');
  try {
    console.log('Consultando herramientas en http://localhost:4000/mcp/v1/tools');
    const response = await axios.get('http://localhost:4000/mcp/v1/tools');
    
    console.log('Respuesta de herramientas:', response);
    console.log('Datos recibidos:', response.data);
    
    // La API devuelve { tools: [...] }
    const toolsData = response.data && response.data.tools ? response.data.tools : [];
    
    if (Array.isArray(toolsData)) {
      // Transformar la lista de herramientas al formato esperado
      tools.value = toolsData.map(toolInfo => {
        console.log('Procesando herramienta:', toolInfo);
        if (typeof toolInfo === 'string') {
          return { name: toolInfo, parameters: [] };
        } else if (typeof toolInfo === 'object' && toolInfo !== null) {
          return { 
            name: toolInfo.name || 'Sin nombre',
            parameters: toolInfo.parameters || [],
            description: toolInfo.description || ''
          };
        }
        return { name: String(toolInfo), parameters: [] };
      });
      
      console.log('Herramientas procesadas:', tools.value);
      console.log('Total de herramientas procesadas:', tools.value.length);
    } else {
      console.warn('La respuesta no contiene un array de herramientas:', response.data);
      tools.value = [];
    }
  } catch (e) {
    console.error('Error al obtener herramientas:', e);
    error.value = 'Error: ' + e.message;
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
    const response = await axios.post(`http://localhost:4000/mcp/v1/tools/${selectedTool.value}/execute`, paramValues.value);
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

const getSelectedToolName = () => {
  if (!selectedTool.value) return '';
  const tool = tools.value.find(t => t.name === selectedTool.value);
  return tool ? tool.name : selectedTool.value;
};

const getSelectedToolDescription = () => {
  if (!selectedTool.value) return '';
  const tool = tools.value.find(t => t.name === selectedTool.value);
  return tool && tool.description ? tool.description : '';
};
</script> 