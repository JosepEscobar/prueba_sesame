# Sistema Multi-Agente para Consultoría Empresarial

Un sistema multi-agente basado en LangGraph y FastAPI para proveer consultoría empresarial especializada a través de agentes inteligentes.

## Características

- **Sistema Modular de Agentes**: Diferentes agentes especializados que trabajan juntos para procesar consultas empresariales
- **Enrutamiento Inteligente**: Distribución automática de consultas al agente más adecuado
- **Integración de Datos**: Consulta de fuentes externas para proporcionar respuestas contextualizadas
- **Observabilidad Integrada**: Métricas y logs estructurados para monitoreo
- **API REST**: Interfaz sencilla para integración con otras aplicaciones

## Agentes Disponibles

- **Router Agent**: Determina qué agente especializado debe procesar cada consulta
- **Analysis Agent**: Especializado en análisis de contenido y extracción de información clave
- **Action Agent**: Enfocado en la implementación de acciones concretas y recomendaciones
- **Summary Agent**: Genera resúmenes concisos de información compleja
- **Finance Agent**: Análisis financiero y consultoría económica
- **Marketing Agent**: Estrategias de marketing y análisis de mercado

## Arquitectura

El sistema está construido con una arquitectura modular:

```
app/
├── agents/             # Agentes especializados
├── api/                # Endpoints de la API REST
├── core/               # Funcionalidades centrales
│   ├── config.py       # Configuración del sistema
│   ├── logging.py      # Sistema de logging
│   ├── metrics.py      # Recolección de métricas
│   └── orchestrator.py # Orquestación de agentes
├── services/           # Servicios externos
└── main.py             # Punto de entrada de la aplicación
```

## Requisitos

- Python 3.11+
- FastAPI
- LangChain
- OpenAI API / Anthropic API
- Prometheus (para métricas)
- Sentry (opcional, para seguimiento de errores)

## Instalación

1. Clone el repositorio:
```bash
git clone https://github.com/usuario/proyecto.git
cd proyecto
```

2. Instale las dependencias:
```bash
pip install -r requirements.txt
```

3. Configure las variables de entorno:
```bash
cp .env.example .env
# Edite el archivo .env con sus claves de API y configuración
```

## Ejecución

### Modo Desarrollo

Para ejecutar la aplicación en modo desarrollo:

```bash
uvicorn app.main:app --reload
```

### Uso con Docker

Para ejecutar la aplicación con Docker y servicios auxiliares (Prometheus, Grafana):

```bash
docker-compose up -d
```

## Uso de la API

### Consulta General

```bash
curl -X POST "http://localhost:8000/api/query" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "¿Cuál es la mejor estrategia de marketing para una startup de tecnología?",
       "context": {
         "company": "TechStartup Inc.",
         "industry": "Software as a Service",
         "target_audience": "Pequeñas y medianas empresas",
         "budget": "Limitado"
       }
     }'
```

### Consultas a Agentes Específicos

Puede especificar un agente preferido (opcional):

```bash
curl -X POST "http://localhost:8000/api/query" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Necesito un análisis financiero para mi empresa de software",
       "agent_preference": "finance_agent",
       "context": {
         "company": "SoftDev Inc.",
         "industry": "Desarrollo de software",
         "revenue": "2.5M",
         "growth_rate": "15%"
       }
     }'
```

## Monitoreo

- **Métricas Prometheus**: Disponibles en `http://localhost:9090`
- **Dashboards Grafana**: Disponibles en `http://localhost:3000` (usuario: admin, contraseña: admin)
- **Documentación API**: Disponible en `http://localhost:8000/docs`

## Contribuciones

Las contribuciones son bienvenidas. Por favor, siga estos pasos:

1. Fork el repositorio
2. Cree una rama para su característica (`git checkout -b feature/nueva-caracteristica`)
3. Haga commit de sus cambios (`git commit -am 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Cree un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo [LICENSE](LICENSE) para más detalles.