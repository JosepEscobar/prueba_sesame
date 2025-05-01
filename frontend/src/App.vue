<template>
  <div class="flex h-screen overflow-hidden bg-black">
    <!-- Sidebar -->
    <div class="w-64 flex flex-col sidebar">
      <div class="p-4 border-b sidebar-header">
        <h1 class="text-xl font-semibold sidebar-title">Sesame Chat</h1>
      </div>
      <nav class="flex-1 overflow-y-auto p-2">
        <div v-for="item in navItems" :key="item.name" class="relative mb-1">
          <RouterLink 
            :to="item.to" 
            class="flex items-center p-3 rounded-lg sidebar-link"
            :class="{ 'sidebar-link-active': isActive(item.to) }"
          >
            <component :is="item.icon" class="w-5 h-5 mr-2 sidebar-icon" />
            {{ item.name }}
          </RouterLink>
          
          <!-- Botón de nuevo chat al lado de Chat -->
          <button 
            v-if="item.name === 'Chat' && isActive(item.to)"
            @click="newChat"
            class="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 sidebar-button rounded-full"
            title="Nuevo chat"
          >
            <PlusCircle class="w-5 h-5" />
          </button>
        </div>
      </nav>
    </div>

    <!-- Main content -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <header class="h-16 flex items-center justify-between px-6 header">
        <h2 class="text-lg font-medium header-title">{{ currentRoute }}</h2>
        <ApiStatus class="w-auto" />
      </header>
      <main class="flex-1 overflow-hidden main-content">
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

<style scoped>
.sidebar {
  background-color: var(--main-surface-background);
  border-right: 1px solid var(--border-light);
}

.sidebar-header {
  border-bottom: 1px solid var(--border-light);
}

.sidebar-title {
  color: var(--sidebar-title-primary);
}

.sidebar-link {
  color: var(--text-secondary);
}

.sidebar-link:hover {
  background-color: var(--surface-hover);
}

.sidebar-link-active {
  background-color: var(--main-surface-secondary-selected);
}

.sidebar-icon {
  color: var(--sidebar-icon);
}

.sidebar-button {
  color: var(--sidebar-icon);
}

.sidebar-button:hover {
  color: var(--text-primary);
  background-color: var(--surface-hover);
}

.header {
  background-color: var(--main-surface-background);
  border-bottom: 1px solid var(--border-light);
}

.header-title {
  color: var(--text-primary);
}

.main-content {
  background-color: var(--main-surface-background);
}
</style> 