from typing import Dict, Any, List
import time
import os
import json

from langchain_core.prompts import ChatPromptTemplate
from app.agents.base import BaseAgent
from app.core.logging import logger
from app.core.config import get_settings

# Definir función para cargar credenciales de manera segura
def load_api_credentials():
    """
    Carga las credenciales de API desde la configuración y maneja posibles errores.
    
    Returns:
        tuple: (openai_key, has_valid_key)
    """
    # Obtener la configuración usando la función cacheada
    settings = get_settings()
    
    # Verificar si hay proxies en las variables de entorno y manejarlos correctamente
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    
    if http_proxy or https_proxy:
        # Configurar las variables de entorno minúsculas usadas por las bibliotecas
        os.environ["http_proxy"] = http_proxy or ""
        os.environ["https_proxy"] = https_proxy or http_proxy or ""
        logger.info("Variables de proxy configuradas en el entorno")
    
    # Verificar si la clave API de OpenAI existe y es válida
    has_valid_key = settings.is_openai_api_key_valid()
    
    if not has_valid_key:
        logger.warning("La API key de OpenAI no está configurada o no es válida. Verifique el archivo .env")
        return None, False
    
    # La clave parece válida
    logger.info("API key de OpenAI cargada correctamente")
    return settings.OPENAI_API_KEY, True

# Cargar las credenciales
openai_api_key, has_openai = load_api_credentials()

# Configurar la API key de OpenAI directamente en el entorno
if has_openai:
    os.environ["OPENAI_API_KEY"] = openai_api_key
    logger.info(f"API key de OpenAI establecida en variables de entorno: {openai_api_key[:5]}...{openai_api_key[-5:] if len(openai_api_key) > 10 else ''}")

# Obtener la configuración completa (usando la función cacheada)
settings = get_settings()

# LLM global usando la API de OpenAI directamente
client = None
try:
    if has_openai:
        from openai import OpenAI
        
        # Inicializar cliente con configuración básica (sin parámetros adicionales)
        client = OpenAI(
            api_key=openai_api_key
        )
        logger.info(f"Cliente OpenAI inicializado correctamente. Modelo configurado: {settings.OPENAI_MODEL}")
except Exception as e:
    has_openai = False
    logger.error(f"Error al inicializar el cliente OpenAI: {str(e)}")

class RouterAgent(BaseAgent):
    """
    Agente Router que determina qué agente especializado debe manejar una consulta.
    
    El Router analiza la consulta entrante y la dirige al agente más adecuado
    basándose en su contenido, contexto y requerimientos específicos.
    """
    
    def __init__(self, model=None):
        """Inicializa el agente router."""
        super().__init__(
            name="router_agent",
            description="Agente de enrutamiento que dirige consultas a agentes especializados."
        )
        # Inicializar atributos
        self.client = None
        
        # Verificamos si tenemos LLM disponible (desde BaseAgent)
        self.has_openai = (self.llm is not None)
        
        # Si no tenemos llm pero tenemos cliente global del módulo, lo usamos
        if not self.has_openai and client is not None:
            self.client = client
            self.has_openai = True
        
        # Asumimos que la conexión es válida para evitar llamadas innecesarias
        # que pueden causdar errores 429 (Too Many Requests)
        logger.info("Omitiendo verificación explícita de conexión para ahorrar llamadas a la API")
        
        # Definir los agentes disponibles y sus capacidades
        self.available_agents = {
            "finance_agent": {
                "description": "Especialista en análisis financiero y consultoría económica.",
                "capabilities": [
                    "análisis financiero",
                    "planificación de presupuestos",
                    "optimización fiscal",
                    "estrategias de inversión",
                    "gestión de riesgos financieros",
                    "valuación empresarial",
                    "análisis de rentabilidad",
                    "modelos financieros",
                    "planificación de flujo de caja"
                ],
                "keywords": [
                    "financiero", "finanzas", "ingresos", "beneficio", "margen", 
                    "roi", "ganancia", "rentabilidad", "balance", "contabilidad",
                    "fiscal", "impuestos", "patrimonio", "capital", "inversión",
                    "activos", "pasivos", "presupuesto", "costes", "gastos"
                ]
            },
            "marketing_agent": {
                "description": "Especialista en estrategias de marketing y análisis de mercado.",
                "capabilities": [
                    "estrategia de marketing",
                    "posicionamiento de marca",
                    "marketing digital",
                    "segmentación de mercado",
                    "análisis competitivo",
                    "estrategia de contenidos",
                    "optimización de canales",
                    "análisis de audiencia",
                    "customer journey",
                    "planificación de campañas"
                ],
                "keywords": [
                    "marketing", "mercado", "campaña", "publicidad", "promoción", 
                    "ventas", "clientes", "segmentación", "conversión", "marca",
                    "audiencia", "consumidor", "target", "posicionamiento", "social",
                    "digital", "comunicación", "medios", "engagement", "producto"
                ]
            },
            "analysis_agent": {
                "description": "Especialista en análisis de información compleja.",
                "capabilities": [
                    "análisis de datos",
                    "procesamiento de documentos",
                    "extracción de insights",
                    "identificación de patrones",
                    "resumen de información",
                    "análisis FODA"
                ],
                "keywords": [
                    "tendencia", "análisis", "analiza", "predicción", "pronóstico",
                    "proyección", "futuro", "evolución", "comparativa", "datos",
                    "información", "patrones", "insights", "métricas", "indicadores",
                    "histórico", "estadística", "correlación", "hallazgos", "síntesis"
                ]
            }
        }
        
        # Definir el sistema de prompt
        self.system_prompt = """Eres un agente router inteligente que decide qué agente especializado debe manejar una consulta empresarial.

# Agentes disponibles

1. Agente de Finanzas (finance_agent) - Para análisis financiero, inversiones, presupuestos, contabilidad, etc.
   Palabras clave: finanzas, financiero, inversión, presupuesto, contabilidad, fiscal, etc.

2. Agente de Marketing (marketing_agent) - Para estrategias de marketing, promoción, publicidad, etc.
   Palabras clave: marketing, mercado, campaña, publicidad, ventas, clientes, etc.

3. Agente de Análisis (analysis_agent) - Para análisis general, tendencias, datos, etc.
   Palabras clave: tendencia, análisis, predicción, datos, información, etc.

Analiza cuidadosamente la consulta del usuario y elige el agente más apropiado en función del contenido.
Responde SOLO con el nombre exacto del agente elegido: "finance_agent", "marketing_agent", o "analysis_agent". No incluyas explicaciones ni otros textos."""
        
        if self.has_openai:
            logger.info(f"RouterAgent inicializado con OpenAI API")
        else:
            logger.warning("RouterAgent inicializado sin OpenAI API. Se usará clasificación por keywords.")
    
    def verify_openai_connection(self):
        """
        DEPRECATED: Método eliminado para evitar llamadas innecesarias a la API.
        Esta función consumía cuota de API sin aportar beneficio real.
        Ahora se asume que la conexión es válida si hay credenciales configuradas.
        """
        # Simplemente devolvemos el estado actual sin hacer llamadas a la API
        return self.has_openai
    
    def _execute_impl(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta el análisis de la consulta y determina qué agente debe procesarla.
        
        Args:
            input_data: Diccionario con los datos de entrada, que debe incluir 'query' y 
                      opcionalmente 'context' y 'agent_preference'
        
        Returns:
            Diccionario con el agente seleccionado, la consulta original y confianza
        """
        start_time = time.time()
        try:
            # Extraer la consulta y el contexto
            query = input_data.get("query", "")
            context = input_data.get("context", {})
            agent_preference = input_data.get("agent_preference")
            
            # Logueamos solo los primeros 50 caracteres de la consulta
            query_preview = query[:50] + "..." if len(query) > 50 else query
            logger.info(f"RouterAgent analizando consulta: {query_preview}")
            
            # Si hay una preferencia de agente, respetarla si el agente existe
            if agent_preference and agent_preference in self.available_agents:
                logger.info(f"Usando agente preferido por el usuario: {agent_preference}")
                return {
                    "agent": agent_preference,
                    "input": input_data,
                    "confidence": 1.0,
                    "reasoning": "Seleccionado por preferencia explícita del usuario"
                }
            
            # Determinar el agente adecuado para la consulta
            agent_type = "analysis_agent"  # Valor por defecto en caso de fallos
            confidence = 0.7  # Confianza predeterminada
            
            # Si tenemos OpenAI configurado, usarlo para clasificar
            if self.has_openai:
                try:
                    # Preparar el prompt con contexto
                    user_prompt = query
                    if context:
                        context_text = "Contexto adicional:\n"
                        for key, value in context.items():
                            context_text += f"- {key}: {value}\n"
                        user_prompt = f"{query}\n\n{context_text}"
                    
                    # Intentar primero con LLM de LangChain si está disponible
                    if self.llm is not None:
                        try:
                            from langchain_core.messages import SystemMessage, HumanMessage
                            
                            messages = [
                                SystemMessage(content=self.system_prompt),
                                HumanMessage(content=user_prompt)
                            ]
                            
                            response = self.invoke_llm(messages, prompt_type="langchain")
                            
                            if response and hasattr(response, 'content'):
                                response_content = response.content.strip()
                                logger.info(f"Respuesta de LangChain LLM: {response_content}")
                                
                                # Validar que la respuesta sea uno de los agentes válidos
                                valid_agents = ["finance_agent", "marketing_agent", "analysis_agent"]
                                if response_content in valid_agents:
                                    agent_type = response_content
                                    confidence = 0.9  # Alta confianza para LLM
                                    logger.info(f"OpenAI clasificó la consulta como: {agent_type} (confianza: {confidence})")
                                else:
                                    # Si la respuesta no es un agente válido, usar keywords
                                    logger.warning(f"OpenAI devolvió respuesta inválida: '{response_content}'. Usando clasificación por keywords.")
                                    agent_type = self._classify_query_by_keywords(query)
                                    confidence = 0.7  # Confianza media para keywords
                            else:
                                # Fallback a cliente directo
                                raise ValueError("Respuesta de LangChain no válida")
                                
                        except Exception as e:
                            logger.warning(f"Error con LangChain: {str(e)}. Usando cliente directo.")
                            # Si falla LangChain, intentar con cliente directo
                            if hasattr(self, 'client') and self.client:
                                # Crear prompt para OpenAI
                                prompt = {
                                    "model": settings.OPENAI_MODEL,
                                    "messages": [
                                        {"role": "system", "content": self.system_prompt},
                                        {"role": "user", "content": user_prompt}
                                    ],
                                    "temperature": settings.TEMPERATURE
                                }
                                
                                # Invocar OpenAI directamente
                                response = self.invoke_llm(prompt, prompt_type="openai_direct")
                                response_content = response.choices[0].message.content.strip()
                                
                                # Validar que la respuesta sea uno de los agentes válidos
                                valid_agents = ["finance_agent", "marketing_agent", "analysis_agent"]
                                if response_content in valid_agents:
                                    agent_type = response_content
                                    confidence = 0.9  # Alta confianza para LLM
                                    logger.info(f"OpenAI clasificó la consulta como: {agent_type} (confianza: {confidence})")
                                else:
                                    # Si la respuesta no es un agente válido, usar keywords
                                    logger.warning(f"OpenAI devolvió respuesta inválida: '{response_content}'. Usando clasificación por keywords.")
                                    agent_type = self._classify_query_by_keywords(query)
                                    confidence = 0.7  # Confianza media para keywords
                            else:
                                # No hay cliente disponible
                                raise ValueError("No hay LLM ni cliente directo disponible")
                    
                    # Si no hay LLM pero hay cliente directo
                    elif hasattr(self, 'client') and self.client:
                        # Crear prompt para OpenAI
                        prompt = {
                            "model": settings.OPENAI_MODEL,
                            "messages": [
                                {"role": "system", "content": self.system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            "temperature": settings.TEMPERATURE
                        }
                        
                        # Invocar OpenAI directamente
                        response = self.invoke_llm(prompt, prompt_type="openai_direct")
                        response_content = response.choices[0].message.content.strip()
                        
                        # Normalizar la respuesta
                        valid_agents = ["finance_agent", "marketing_agent", "analysis_agent"]
                        if response_content in valid_agents:
                            agent_type = response_content
                            confidence = 0.9  # Alta confianza para LLM
                            logger.info(f"OpenAI clasificó la consulta como: {agent_type} (confianza: {confidence})")
                        else:
                            # Si la respuesta no es un agente válido, usar keywords
                            logger.warning(f"OpenAI devolvió respuesta inválida: '{response_content}'. Usando clasificación por keywords.")
                            agent_type = self._classify_query_by_keywords(query)
                            confidence = 0.7  # Confianza media para keywords
                except Exception as e:
                    logger.error(f"Error al invocar OpenAI: {str(e)}. Usando clasificación por keywords.")
                    agent_type = self._classify_query_by_keywords(query)
                    confidence = 0.7  # Confianza media para keywords
            else:
                # Si no hay OpenAI, usar clasificación por keywords
                agent_type = self._classify_query_by_keywords(query)
                logger.info(f"RouterAgent clasificó la consulta como {agent_type} usando keywords")
            
            # Verificación final para garantizar que agent_type siempre tenga un valor
            if not agent_type:
                logger.warning("No se pudo determinar un tipo de agente. Usando 'analysis_agent' por defecto.")
                agent_type = "analysis_agent"
            
            # Imprimir para depuración
            print(f"*** AGENT_TYPE FINAL: {agent_type} ***")
            
            # Crear la decisión
            decision = {
                "agent": agent_type,  # Este es el campo clave que debe estar presente
                "input": input_data,
                "confidence": confidence,
                "reasoning": "Clasificado por análisis de la consulta"
            }
            
            # Imprimir para depuración
            print(f"*** DECISION FINAL: {decision} ***")
            
            return decision
            
        except Exception as e:
            logger.error(f"Error en RouterAgent: {str(e)}")
            return {
                "error": f"Error en enrutamiento: {str(e)}",
                "agent": "analysis_agent",  # Valor por defecto en caso de error
                "input": input_data,
                "confidence": 0.0
            }
    
    def _classify_query_by_keywords(self, query: str) -> str:
        """
        Clasifica una consulta usando LLM o, como fallback, por palabras clave.
        
        Args:
            query: La consulta a clasificar
        
        Returns:
            El tipo de agente más adecuado
        """
        # Intentar usar LLM si está disponible para categorización JSON
        if self.llm is not None:
            try:
                categorization_prompt = f"""
                Analiza la siguiente consulta y determina qué agente especializado debería manejarla.
                
                Consulta: "{query}"
                
                Devuelve SOLAMENTE un objeto JSON con esta estructura:
                {{
                    "agent": "finance_agent" | "marketing_agent" | "analysis_agent",
                    "confidence": float entre 0 y 1,
                    "reasoning": "breve explicación de la elección"
                }}
                
                Criterios para cada agente:
                - finance_agent: Consultas sobre finanzas, inversiones, contabilidad, análisis financiero, presupuestos, etc.
                - marketing_agent: Consultas sobre marketing, publicidad, campañas, estrategias de mercado, clientes, etc.
                - analysis_agent: Consultas generales de análisis, tendencias, datos, información general, etc.
                
                No incluyas texto adicional en tu respuesta, solo el JSON.
                """
                
                response = self.llm.invoke(categorization_prompt)
                categorization = json.loads(response.content.strip())
                logger.info(f"Categorización por LLM: {categorization}")
                
                agent_type = categorization.get("agent", "analysis_agent")
                logger.info(f"LLM seleccionó agente: {agent_type}")
                
                return agent_type
                
            except Exception as e:
                logger.error(f"Error al usar LLM para categorización JSON: {str(e)}. Usando clasificación por keywords como fallback.")
                # Continuar con el método de palabras clave como fallback
        
        # Fallback: clasificación por palabras clave
        # Convertir la consulta a minúsculas
        query_lower = query.lower()
        
        # Calcular puntuaciones para cada agente
        scores = {}
        for agent_name, agent_info in self.available_agents.items():
            keywords = agent_info.get("keywords", [])
            score = sum(1 for kw in keywords if kw in query_lower)
            scores[agent_name] = score
        
        # Encontrar el agente con mayor puntuación
        if not scores:
            return "analysis_agent"  # Por defecto
            
        max_score = max(scores.values())
        if max_score == 0:
            return "analysis_agent"  # Si ninguno tiene keywords, usar análisis
            
        # Si hay múltiples con la misma puntuación máxima, priorizar en este orden
        priority = ["finance_agent", "marketing_agent", "analysis_agent"]
        max_agents = [agent for agent, score in scores.items() if score == max_score]
        
        for p in priority:
            if p in max_agents:
                return p
                
        # Si ninguno de los priorizados está en los máximos, tomar el primero
        return max_agents[0] 