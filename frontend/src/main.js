import { createApp } from 'vue';
import { createPinia } from 'pinia';
import axios from 'axios';
import App from './App.vue';
import router from './router';
import './assets/main.css';

// Configuración global de axios
axios.defaults.baseURL = 'http://localhost:8000';
axios.defaults.timeout = 10000; // 10 segundos
axios.interceptors.response.use(
    response => response,
    error => {
        console.error('Error de API:', error);
        return Promise.reject(error);
    }
);

const app = createApp(App);

app.use(createPinia());
app.use(router);

app.mount('#app'); 