<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-4xl mx-auto">
    <div v-for="(suggestion, index) in suggestions" :key="index"
         class="suggestion-card" @click="selectSuggestion(suggestion)">
      <div class="flex items-center mb-2">
        <div class="icon-container">
          <component :is="suggestion.icon" class="w-5 h-5" />
        </div>
        <span class="text-base font-medium ml-3 text-gray-100">{{ suggestion.title }}</span>
      </div>
      <p class="text-gray-400 text-sm">{{ suggestion.text }}</p>
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
  Megaphone,
  DollarSign,
  List,
  ShieldAlert,
  Globe
} from 'lucide-vue-next';

const emit = defineEmits(['select']);

const selectSuggestion = (suggestion) => {
  if (suggestion.jsonQuery) {
    emit('select', suggestion.jsonQuery);
  } else {
    emit('select', suggestion.text);
  }
};

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
  },
  {
    title: 'Pronóstico Financiero con ingresos',
    text: 'Proporciona un análisis financiero para una empresa de software con ingresos de 5 millones',
    icon: DollarSign,
    jsonQuery: '{"query": "Proporciona un análisis financiero para una empresa de software con ingresos de 5 millones"}'
  },
  {
    title: 'Análisis de Acciones',
    text: '¿Qué acciones debo tomar para mejorar la tasa de conversión en mi sitio web de e-commerce?',
    icon: List,
    jsonQuery: '{"query": "¿Qué acciones debo tomar para mejorar la tasa de conversión en mi sitio web de e-commerce?"}'
  },
  {
    title: 'Guarda rail',
    text: '¿Cuales son los ingredientes de una paella?',
    icon: ShieldAlert,
    jsonQuery: '{"query": "¿Cuales son los ingredientes de una paella?"}'
  },
  {
    title: 'Guarda rail',
    text: '¿Por que la tierra es esférica?',
    icon: Globe,
    jsonQuery: '{"query": "¿Por que la tierra es esférica?"}'
  }
];
</script>

<style scoped>
.suggestion-card {
  @apply p-4 rounded-lg shadow hover:shadow-lg transition-shadow border cursor-pointer;
  background-color: var(--message-surface);
  border-color: var(--border-light);
}

.suggestion-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-medium);
}

.icon-container {
  @apply flex items-center justify-center w-8 h-8 rounded-full;
  background-color: var(--composer-blue-bg);
  color: var(--composer-blue-text);
}
</style> 