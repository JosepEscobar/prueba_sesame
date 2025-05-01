# Sesame Chat UI

Interfaz de usuario tipo ChatGPT para la API de Sesame, desarrollada con Vue.js.

## Características

- Diseño inspirado en ChatGPT
- Interfaz de chat para interactuar con la API de Sesame
- Visualización de estado del sistema
- Herramientas específicas para:
  - Consultas financieras (análisis y pronósticos)
  - Marketing (análisis y generación de campañas)
  - Exploración de herramientas MCP

## Interacción con Agentes del Sistema

La interfaz permite interactuar con los diferentes agentes de Sesame de forma transparente:

- **Consultas generales**: El sistema automáticamente enruta la consulta al agente más adecuado.
- **Consultas financieras**: Dirigidas al Finance Agent para análisis financiero.
- **Consultas de marketing**: Procesadas por el Marketing Agent para estrategias y análisis.
- **Análisis de datos**: Manejadas por el Analysis Agent para tendencias y patrones.
- **Información del sistema**: El System Info Agent proporciona detalles sobre capacidades y estado.

### Ejemplos de Consultas

- "¿Cuáles son las capacidades de la API de Sesame?" → System Info Agent
- "Analiza los ratios financieros de Apple" → Finance Agent
- "Recomienda una estrategia de marketing para una startup" → Marketing Agent
- "Identifica tendencias en este conjunto de datos" → Analysis Agent

## Panel de Estado del Sistema

El frontend incluye un panel dedicado a mostrar el estado del sistema con:

- Estado de los servicios (API Server, MCP Server)
- Distribución de consultas por agente
- Métricas de rendimiento en tiempo real
- Alertas y notificaciones

La información se actualiza en tiempo real gracias a la integración con las métricas de Prometheus.

## Tecnologías

- Vue.js 3
- Vue Router
- Pinia (gestión de estado)
- Tailwind CSS (estilos)
- Axios (peticiones HTTP)
- Lucide Icons (iconografía)

## Estructura del Proyecto

```
frontend/
├── public/               # Archivos estáticos
├── src/
│   ├── api/              # Servicios de API
│   ├── assets/           # Recursos (CSS, imágenes)
│   ├── components/       # Componentes reutilizables
│   ├── router/           # Configuración de rutas
│   ├── views/            # Vistas principales
│   ├── App.vue           # Componente raíz
│   └── main.js           # Punto de entrada
├── index.html            # Plantilla HTML
├── package.json          # Dependencias
├── tailwind.config.js    # Configuración de Tailwind
└── vite.config.js        # Configuración de Vite
```

## Instalación

1. Asegúrate de tener Node.js instalado (v14 o superior)
2. Clona este repositorio
3. Instala las dependencias:

```bash
cd frontend
npm install
```

## Desarrollo

Para iniciar el servidor de desarrollo:

```bash
npm run dev
```

Esto iniciará el servidor en `http://localhost:5173` (o el siguiente puerto disponible).

## Construcción para Producción

```bash
npm run build
```

Los archivos compilados se guardarán en la carpeta `dist/`.

## Vista Previa de Producción

Para previsualizar la versión de producción localmente:

```bash
npm run preview
```

## Conexión con la API de Sesame

La aplicación se comunica con la API de Sesame a través de endpoints definidos. Asegúrate de que la API esté en funcionamiento y accesible. La configuración del proxy está en `vite.config.js` y apunta a `http://localhost:8000` por defecto. 

