<template>
  <div class="h-full p-6 overflow-y-auto">
    <div class="max-w-4xl mx-auto">
      <h2 class="text-xl font-semibold mb-4">Estado del Sistema</h2>
      
      <!-- Estado general de la API -->
      <div style="background-color: var(--message-surface);" class="shadow rounded-lg p-6 mb-6">
        <h3 class="text-lg font-medium mb-4">Estado General</h3>
        
        <div class="flex items-center mb-4">
          <div :class="statusColorClass" class="w-4 h-4 rounded-full mr-3"></div>
          <div>
            <div class="font-medium">API Sesame</div>
            <div class="text-sm text-gray-600 dark:text-gray-400">{{ healthText }}</div>
          </div>
          <button 
            @click="fetchHealthStatus" 
            class="ml-auto p-2 text-gray-300 hover:text-white"
            title="Refrescar"
          >
            <RefreshCw class="w-5 h-5" />
          </button>
        </div>
        
        <div v-if="healthDetails" class="text-sm text-gray-600 dark:text-gray-400 mt-2">
          <div><span class="font-medium">Última actualización:</span> {{ formatTime(lastUpdate) }}</div>
          <div v-if="healthDetails.version">
            <span class="font-medium">Versión:</span> {{ healthDetails.version }}
          </div>
          <div v-if="healthDetails.mcp_status">
            <span class="font-medium">Estado MCP:</span> {{ healthDetails.mcp_status }}
          </div>
        </div>
      </div>
      
      <!-- MCP Status -->
      <div style="background-color: var(--message-surface);" class="shadow rounded-lg p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-medium">MCP</h3>
          <button 
            @click="fetchMcpStatus" 
            class="p-2 text-gray-300 hover:text-white"
            title="Refrescar"
          >
            <RefreshCw class="w-5 h-5" />
          </button>
        </div>
        
        <div v-if="isLoadingMcp" class="flex justify-center py-4">
          <div class="animate-spin text-primary-500">
            <RefreshCw class="w-6 h-6" />
          </div>
        </div>
        
        <div v-else-if="mcpError" class="text-red-500 text-sm">
          {{ mcpError }}
        </div>
        
        <div v-else-if="mcpStatus" class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div style="background-color: #292929;" class="p-4 rounded-lg">
              <div class="text-sm font-medium mb-1">URL</div>
              <div class="text-gray-200">{{ mcpStatus.mcp_url || 'No disponible' }}</div>
            </div>
            
            <div style="background-color: #292929;" class="p-4 rounded-lg">
              <div class="text-sm font-medium mb-1">Estado</div>
              <div class="flex items-center">
                <div 
                  :class="mcpStatus.status === 'connected' ? 'bg-green-500' : 'bg-red-500'" 
                  class="w-3 h-3 rounded-full mr-2"
                ></div>
                <span>{{ mcpStatus.status === 'connected' ? 'Conectado' : 'Desconectado' }}</span>
              </div>
            </div>
          </div>
          
          <div v-if="mcpStatus.tools && mcpStatus.tools.length" class="mt-4">
            <h4 class="font-medium mb-2">Herramientas Disponibles ({{ mcpStatus.tools_available }})</h4>
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              <div 
                v-for="tool in mcpStatus.tools" 
                :key="tool"
                style="background-color: #292929;"
                class="flex items-center p-3 rounded-lg"
              >
                <Wrench class="w-4 h-4 text-gray-300 mr-2 flex-shrink-0" />
                <div class="min-w-0">
                  <div class="font-medium text-sm truncate">{{ typeof tool === 'string' ? tool : tool.name }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else class="text-gray-500 dark:text-gray-400 text-center py-4">
          No hay información disponible
        </div>
      </div>
      
      <!-- Endpoints disponibles -->
      <div style="background-color: var(--message-surface);" class="shadow rounded-lg p-6">
        <h3 class="text-lg font-medium mb-4">Endpoints Disponibles</h3>
        
        <div class="space-y-4">
          <div v-for="(endpoints, category) in apiEndpoints" :key="category" class="border-b border-gray-200 dark:border-gray-700 pb-4 last:border-0">
            <h4 class="font-medium mb-2">{{ category }}</h4>
            <div class="space-y-2">
              <div 
                v-for="endpoint in endpoints" 
                :key="endpoint.path"
                style="background-color: #292929;"
                class="p-3 rounded-lg"
              >
                <div class="flex items-center">
                  <span 
                    :class="{
                      'bg-green-200 text-green-800 dark:bg-green-900 dark:text-green-200': endpoint.method === 'GET',
                      'bg-blue-200 text-blue-800 dark:bg-blue-900 dark:text-blue-200': endpoint.method === 'POST',
                      'bg-yellow-200 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200': endpoint.method === 'PUT',
                      'bg-red-200 text-red-800 dark:bg-red-900 dark:text-red-200': endpoint.method === 'DELETE'
                    }"
                    class="inline-block px-2 py-1 rounded text-xs font-medium mr-2"
                  >
                    {{ endpoint.method }}
                  </span>
                  <span class="font-mono text-sm">{{ endpoint.path }}</span>
                </div>
                <p v-if="endpoint.description" class="text-sm text-gray-400 mt-1">
                  {{ endpoint.description }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Endpoints MCP Server -->
      <div style="background-color: var(--message-surface);" class="shadow rounded-lg p-6 mt-6">
        <h3 class="text-lg font-medium mb-4">Endpoints MCP Server</h3>
        <div class="space-y-4">
          <div v-for="(endpoints, category) in mcpEndpoints" :key="'mcp-'+category" class="border-b border-gray-200 dark:border-gray-700 pb-4 last:border-0">
            <h4 class="font-medium mb-2">{{ category }}</h4>
            <div class="space-y-2">
              <div 
                v-for="endpoint in endpoints" 
                :key="endpoint.path"
                style="background-color: #292929;"
                class="p-3 rounded-lg"
              >
                <div class="flex items-center">
                  <span 
                    :class="{
                      'bg-green-200 text-green-800 dark:bg-green-900 dark:text-green-200': endpoint.method === 'GET',
                      'bg-blue-200 text-blue-800 dark:bg-blue-900 dark:text-blue-200': endpoint.method === 'POST',
                      'bg-yellow-200 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200': endpoint.method === 'PUT',
                      'bg-red-200 text-red-800 dark:bg-red-900 dark:text-red-200': endpoint.method === 'DELETE'
                    }"
                    class="inline-block px-2 py-1 rounded text-xs font-medium mr-2"
                  >
                    {{ endpoint.method }}
                  </span>
                  <span class="font-mono text-sm">{{ endpoint.path }}</span>
                </div>
                <p v-if="endpoint.description" class="text-sm text-gray-400 mt-1">
                  {{ endpoint.description }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import axios from 'axios';
import { RefreshCw, Wrench } from 'lucide-vue-next';

// Estado de salud
const health = ref('loading');
const healthDetails = ref(null);
const lastUpdate = ref(new Date());
const isLoading = ref(false);

// Estado MCP
const mcpStatus = ref(null);
const isLoadingMcp = ref(false);
const mcpError = ref(null);

// Temporizador para actualización automática
let refreshTimer = null;

// Endpoints dinámicos según OpenAPI
const apiEndpoints = ref({});
const mcpEndpoints = ref({});

// Montar y limpiar
onMounted(() => {
  fetchHealthStatus();
  fetchMcpStatus();
  fetchApiEndpoints();
  fetchMcpEndpoints();
  
  // Actualizar cada 30 segundos
  refreshTimer = setInterval(() => {
    fetchHealthStatus();
    fetchMcpStatus();
    fetchApiEndpoints();
    fetchMcpEndpoints();
  }, 30000);
});

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
});

// Obtener estado de salud
const fetchHealthStatus = async () => {
  isLoading.value = true;
  
  try {
    const response = await axios.get('/health');
    health.value = response.data.status || 'unhealthy';
    healthDetails.value = response.data;
    lastUpdate.value = new Date();
  } catch (error) {
    health.value = 'unhealthy';
    console.error('Error al obtener estado de salud:', error);
  } finally {
    isLoading.value = false;
  }
};

// Obtener estado MCP
const fetchMcpStatus = async () => {
  isLoadingMcp.value = true;
  mcpError.value = null;
  
  try {
    const response = await axios.get('/mcp/status');
    
    if (response && response.data) {
      mcpStatus.value = {
        status: response.data.status || 'disconnected',
        mcp_url: response.data.mcp_url || '',
        tools_available: response.data.tools_available || 0,
        tools: response.data.tools || []
      };
    }
  } catch (error) {
    mcpError.value = 'No se pudo obtener el estado del MCP: ' + (error.response?.data?.message || error.message);
    console.error('Error al obtener estado de MCP:', error);
    
    // En caso de error, marcar como desconectado pero no nulo
    mcpStatus.value = {
      status: 'disconnected',
      mcp_url: '',
      tools_available: 0,
      tools: []
    };
  } finally {
    isLoadingMcp.value = false;
  }
};

// Texto de estado de salud
const healthText = computed(() => {
  if (health.value === 'loading') return 'Cargando...';
  return {
    'healthy': 'Funcionando correctamente',
    'degraded': 'Funcionando con degradación',
    'unhealthy': 'No disponible'
  }[health.value] || 'Estado desconocido';
});

// Clase de color para estado
const statusColorClass = computed(() => {
  return {
    'loading': 'bg-gray-300 animate-pulse',
    'healthy': 'bg-green-500',
    'degraded': 'bg-yellow-500',
    'unhealthy': 'bg-red-500'
  }[health.value] || 'bg-gray-500';
});

// Formatear tiempo
const formatTime = (time) => {
  if (!time) return '';
  
  const date = new Date(time);
  return date.toLocaleString();
};

// Formatear tiempo de actividad
const formatUptime = (uptime) => {
  if (!uptime) return '';
  
  const seconds = Math.floor(uptime);
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  const parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);
  
  return parts.join(' ');
};

// Carga de endpoints desde /api/openapi.json
const fetchApiEndpoints = async () => {
  try {
    const res = await axios.get('/api/openapi.json');
    const paths = res.data.paths || {};
    const grouped = {};
    Object.entries(paths).forEach(([path, methods]) => {
      Object.entries(methods).forEach(([method, info]) => {
        const tags = info.tags || ['General'];
        tags.forEach(tag => {
          if (!grouped[tag]) grouped[tag] = [];
          grouped[tag].push({
            method: method.toUpperCase(),
            path,
            description: info.summary || info.description || ''
          });
        });
      });
    });
    apiEndpoints.value = grouped;
  } catch (e) {
    console.error('Error cargando OpenAPI spec API:', e);
    // Datos de ejemplo en caso de error
    apiEndpoints.value = {
      'General': [
        { method: 'GET', path: '/health', description: 'Verificar estado de la API' },
        { method: 'GET', path: '/api/v1/agents', description: 'Listar agentes disponibles' },
        { method: 'POST', path: '/api/v1/query', description: 'Procesar consulta de usuario' }
      ],
      'Monitoreo': [
        { method: 'GET', path: '/metrics', description: 'Métricas de Prometheus' },
        { method: 'GET', path: '/mcp/status', description: 'Estado de conexión con MCP' }
      ]
    };
  }
};

// Carga de endpoints desde /mcp/openapi.json
const fetchMcpEndpoints = async () => {
  try {
    const res = await axios.get('/mcp/openapi.json');
    const paths = res.data.paths || {};
    const grouped = {};
    Object.entries(paths).forEach(([path, methods]) => {
      Object.entries(methods).forEach(([method, info]) => {
        const tags = info.tags || ['General'];
        tags.forEach(tag => {
          if (!grouped[tag]) grouped[tag] = [];
          grouped[tag].push({
            method: method.toUpperCase(),
            path,
            description: info.summary || info.description || ''
          });
        });
      });
    });
    mcpEndpoints.value = grouped;
  } catch (e) {
    console.error('Error cargando OpenAPI spec MCP:', e);
    // Datos de ejemplo en caso de error
    mcpEndpoints.value = {
      'MCP': [
        { method: 'GET', path: '/status', description: 'Estado del servidor MCP' },
        { method: 'GET', path: '/tools', description: 'Listar herramientas disponibles' }
      ],
      'Herramientas': [
        { method: 'POST', path: '/tools/buscar_datos_financieros', description: 'Buscar datos financieros de empresas' },
        { method: 'POST', path: '/tools/calcular_ratios_financieros', description: 'Calcular ratios financieros' },
        { method: 'POST', path: '/tools/analizar_rendimiento_campania', description: 'Analizar rendimiento de campaña' },
        { method: 'POST', path: '/tools/recomendar_estrategia_marketing', description: 'Recomendar estrategia de marketing' },
        { method: 'POST', path: '/tools/analizar_tendencia', description: 'Analizar tendencia de datos' },
        { method: 'POST', path: '/tools/predecir_valores', description: 'Predecir valores futuros' }
      ]
    };
  }
};
</script> 