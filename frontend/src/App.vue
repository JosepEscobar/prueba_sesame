<template>
  <div class="flex h-screen overflow-hidden">
    <!-- Sidebar -->
    <div class="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      <div class="p-4 border-b border-gray-200 dark:border-gray-700">
        <h1 class="text-xl font-semibold">Sesame Chat</h1>
      </div>
      <nav class="flex-1 overflow-y-auto p-2">
        <div v-for="item in navItems" :key="item.name" class="relative mb-1">
          <RouterLink 
            :to="item.to" 
            class="flex items-center p-3 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            :class="{ 'bg-gray-100 dark:bg-gray-700': isActive(item.to) }"
          >
            <component :is="item.icon" class="w-5 h-5 mr-2" />
            {{ item.name }}
          </RouterLink>
          
          <!-- Botón de nuevo chat al lado de Chat -->
          <button 
            v-if="item.name === 'Chat' && isActive(item.to)"
            @click="newChat"
            class="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600"
            title="Nuevo chat"
          >
            <PlusCircle class="w-5 h-5" />
          </button>
        </div>
      </nav>
    </div>

    <!-- Main content -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <header class="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6">
        <h2 class="text-lg font-medium">{{ currentRoute }}</h2>
        <ApiStatus class="w-auto" />
      </header>
      <main class="flex-1 overflow-hidden bg-gray-50 dark:bg-gray-900">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { RouterLink, RouterView, useRoute } from 'vue-router';
import { MessageSquare, Wrench, BarChart, Megaphone, Activity, PlusCircle } from 'lucide-vue-next';
import ApiStatus from './components/ApiStatus.vue';

const route = useRoute();

const navItems = [
  { name: 'Chat', to: '/', icon: MessageSquare },
  { name: 'Herramientas', to: '/tools', icon: Wrench },
  { name: 'Finanzas', to: '/finance', icon: BarChart },
  { name: 'Marketing', to: '/marketing', icon: Megaphone },
  { name: 'Estado', to: '/status', icon: Activity }
];

const currentRoute = computed(() => {
  const current = navItems.find(item => item.to === route.path);
  return current ? current.name : 'Chat';
});

const isActive = (path) => {
  return route.path === path;
};

const newChat = () => {
  window.location.reload();
};
</script> 