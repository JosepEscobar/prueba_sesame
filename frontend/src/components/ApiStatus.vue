<template>
  <div class="p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
    <h3 class="text-sm font-medium mb-2">Estado del Sistema</h3>
    
    <div class="flex items-center mb-2">
      <div :class="statusColorClass" class="w-3 h-3 rounded-full mr-2"></div>
      <span class="text-sm">API: {{ healthText }}</span>
    </div>
    
    <div v-if="mcpStatus" class="mt-3 border-t border-gray-200 dark:border-gray-700 pt-2">
      <h4 class="text-xs font-medium mb-1">MCP</h4>
      <div class="text-xs text-gray-600 dark:text-gray-400">
        <div>URL: {{ mcpStatus.url || 'No disponible' }}</div>
        <div v-if="mcpStatus.tools && mcpStatus.tools.length" class="mt-1">
          <div class="mb-1">Herramientas:</div>
          <div class="flex flex-wrap gap-1">
            <span 
              v-for="tool in mcpStatus.tools" 
              :key="tool.name"
              class="inline-block px-2 py-0.5 bg-secondary-100 dark:bg-secondary-800 rounded text-xs"
            >
              {{ tool.name }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

const health = ref('loading');
const mcpStatus = ref(null);

// Obtener estados al montar
onMounted(async () => {
  try {
    await fetchHealthStatus();
    await fetchMcpStatus();
    
    // Actualizar cada 30 segundos
    setInterval(async () => {
      await fetchHealthStatus();
      await fetchMcpStatus();
    }, 30000);
  } catch (error) {
    console.error('Error al obtener estado inicial:', error);
  }
});

const fetchHealthStatus = async () => {
  try {
    const response = await axios.get('/health');
    health.value = response.data.status || 'unhealthy';
  } catch (error) {
    health.value = 'unhealthy';
    console.error('Error al obtener estado de salud:', error);
  }
};

const fetchMcpStatus = async () => {
  try {
    const response = await axios.get('/mcp/status');
    mcpStatus.value = response.data;
  } catch (error) {
    mcpStatus.value = null;
    console.error('Error al obtener estado de MCP:', error);
  }
};

const healthText = computed(() => {
  if (health.value === 'loading') return 'Cargando...';
  return {
    'healthy': 'En línea',
    'degraded': 'Degradado',
    'unhealthy': 'Fuera de línea'
  }[health.value] || 'Desconocido';
});

const statusColorClass = computed(() => {
  return {
    'loading': 'bg-gray-300 animate-pulse',
    'healthy': 'bg-green-500',
    'degraded': 'bg-yellow-500',
    'unhealthy': 'bg-red-500'
  }[health.value] || 'bg-gray-500';
});
</script> 