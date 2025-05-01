<template>
  <div class="flex items-center text-sm">
    <div class="flex items-center mr-3">
      <div :class="statusColorClass" class="w-2 h-2 rounded-full mr-2"></div>
      <span class="text-gray-300">API</span>
    </div>
    
    <div v-if="mcpStatus" class="flex items-center">
      <div class="mx-2 text-gray-500">|</div>
      <div class="flex items-center">
        <div 
          :style="mcpStatus.status === 'connected' ? 'background-color: #22c55e' : 'background-color: #ef4444'" 
          class="w-2 h-2 rounded-full mr-2"
        ></div>
        <span class="text-gray-300">MCP</span>
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
    console.log('Consultando estado de salud en http://localhost:8000/health');
    const response = await axios.get('/health');
    health.value = response.data.status || 'unhealthy';
  } catch (error) {
    health.value = 'unhealthy';
    console.error('Error al obtener estado de salud:', error);
  }
};

const fetchMcpStatus = async () => {
  try {
    console.log('Consultando estado MCP en http://localhost:8000/mcp/status');
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
    'loading': 'bg-gray-400 animate-pulse',
    'healthy': 'bg-green-500',
    'degraded': 'bg-yellow-500',
    'unhealthy': 'bg-red-500'
  }[health.value] || 'bg-gray-500';
});
</script> 