<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-4xl mx-auto">
    <div v-for="(suggestion, index) in suggestions" :key="index"
         class="suggestion-card" @click="$emit('select', suggestion.text)">
      <div class="flex items-center mb-2">
        <div class="icon-container">
          <component :is="suggestion.icon" class="w-5 h-5" />
        </div>
        <span class="text-base font-medium ml-3">{{ suggestion.title }}</span>
      </div>
      <p class="text-gray-600 dark:text-gray-400 text-sm">{{ suggestion.text }}</p>
    </div>
  </div>
</template>

<script setup>
import { 
  MessageCircle, 
  Search, 
  BarChart2, 
  TrendingUp, 
  Users,
  Megaphone
} from 'lucide-vue-next';

const emit = defineEmits(['select']);

const suggestions = [
  {
    title: 'Chat General',
    text: '¿Cuáles son las capacidades de la API de Sesame?',
    icon: MessageCircle
  },
  {
    title: 'Estado del Sistema',
    text: '¿Cuál es el estado actual del servicio?',
    icon: Search
  },
  {
    title: 'Análisis Financiero',
    text: 'Analiza nuestros ingresos del último trimestre',
    icon: BarChart2
  },
  {
    title: 'Pronóstico Financiero',
    text: 'Genera un pronóstico de ventas para el próximo mes',
    icon: TrendingUp
  },
  {
    title: 'Análisis de Marketing',
    text: 'Analiza el rendimiento de nuestra última campaña',
    icon: Megaphone
  },
  {
    title: 'Campaña de Marketing',
    text: 'Sugiere una nueva estrategia para aumentar nuestro alcance en redes sociales',
    icon: Users
  }
];
</script>

<style scoped>
.suggestion-card {
  @apply p-4 rounded-lg bg-gray-50 dark:bg-gray-800 shadow hover:shadow-lg transition-shadow 
         border border-gray-200 dark:border-gray-700 cursor-pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.suggestion-card:hover {
  transform: translateY(-2px);
  @apply border-primary-300 dark:border-primary-700;
}

.icon-container {
  @apply flex items-center justify-center w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400;
}
</style> 