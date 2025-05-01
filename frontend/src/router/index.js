import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: () => import('../views/ChatView.vue')
        },
        {
            path: '/tools',
            name: 'tools',
            component: () => import('../views/ToolsView.vue')
        },
        {
            path: '/finance',
            name: 'finance',
            component: () => import('../views/FinanceView.vue')
        },
        {
            path: '/marketing',
            name: 'marketing',
            component: () => import('../views/MarketingView.vue')
        },
        {
            path: '/status',
            name: 'status',
            component: () => import('../views/StatusView.vue')
        }
    ]
});

export default router; 