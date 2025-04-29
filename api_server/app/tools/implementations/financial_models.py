"""
Implementación de herramienta para obtener modelos financieros.
"""

from typing import Dict, Any, List
import random

class FinancialModelsImplementation:
    """
    Implementación de la herramienta para obtener modelos o plantillas financieras para diferentes industrias.
    """
    
    def __init__(self):
        """Inicializa la implementación con datos de ejemplo."""
        self.model_categories = {
            "cash_flow": "Modelos de flujo de caja para gestionar entradas y salidas de efectivo",
            "valuation": "Modelos de valoración de empresas y activos",
            "budget": "Plantillas para presupuestos empresariales",
            "forecast": "Modelos para proyecciones financieras",
            "investment": "Análisis de inversiones y retornos",
            "pricing": "Modelos para estrategias de precios",
            "breakeven": "Análisis de punto de equilibrio",
            "roi": "Cálculo de retorno sobre la inversión"
        }
        
        self.industries = [
            "technology", "finance", "healthcare", "retail", "manufacturing", 
            "real_estate", "education", "hospitality", "general"
        ]
        
        # Datos de ejemplo para modelos financieros
        self.sample_models = self._generate_sample_models()
    
    def _generate_sample_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """Genera datos de ejemplo para los modelos financieros."""
        models_by_category = {}
        
        for category in self.model_categories.keys():
            models = []
            for i in range(1, 5):  # 4 modelos por categoría
                for industry in random.sample(self.industries, 3):  # 3 industrias aleatorias
                    models.append({
                        "name": f"{category.title()} {i} - {industry.title()}",
                        "description": f"Modelo de {self.model_categories[category]} para {industry}",
                        "format": random.choice(["excel", "google_sheets", "pdf"]),
                        "complexity": random.choice(["basic", "intermediate", "advanced"]),
                        "creator": "Sesame Financial Models",
                        "last_updated": "2025-01-15",
                        "download_url": f"https://example.com/financial-models/{category}/{industry}/download",
                        "preview_url": f"https://example.com/financial-models/{category}/{industry}/preview",
                        "tags": [category, industry, "finance", "model"]
                    })
            models_by_category[category] = models
        
        return models_by_category
    
    def get_models(self, model_type: str, industry: str = "general", 
                  complexity: str = "intermediate", format: str = "excel") -> Dict[str, Any]:
        """
        Obtiene modelos financieros según los criterios especificados.
        
        Args:
            model_type: Tipo de modelo financiero (cash_flow, valuation, etc.)
            industry: Industria específica para el modelo
            complexity: Nivel de complejidad del modelo
            format: Formato de salida deseado
            
        Returns:
            Diccionario con modelos financieros que cumplen los criterios
        """
        try:
            # Validar el tipo de modelo
            if model_type not in self.model_categories:
                return {
                    "error": f"Tipo de modelo no válido: {model_type}",
                    "valid_types": list(self.model_categories.keys())
                }
            
            # Filtrar modelos por tipo
            all_models = self.sample_models.get(model_type, [])
            
            # Filtrar por industria, complejidad y formato
            filtered_models = []
            for model in all_models:
                if (industry == "general" or industry in model["tags"] or 
                    model["tags"][1] == industry):
                    if complexity == model["complexity"] or complexity == "intermediate":
                        if format == model["format"] or format == "excel":
                            filtered_models.append(model)
            
            # Generar recomendaciones
            recommendations = []
            if filtered_models:
                for i, model in enumerate(filtered_models[:2]):
                    recommendations.append({
                        "model_id": f"{model['name'].lower().replace(' ', '_')}",
                        "reason": f"Recomendado para {industry} con nivel de complejidad {complexity}"
                    })
            
            return {
                "models": filtered_models,
                "recommendations": recommendations,
                "total_results": len(filtered_models)
            }
            
        except Exception as e:
            return {
                "error": f"Error al obtener modelos financieros: {str(e)}"
            }
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método para compatibilidad con el servidor MCP.
        
        Args:
            params: Parámetros para la herramienta
            
        Returns:
            Resultados de la herramienta
        """
        model_type = params.get("model_type", "")
        industry = params.get("industry", "general")
        complexity = params.get("complexity", "intermediate")
        format = params.get("format", "excel")
        
        return self.get_models(model_type, industry, complexity, format) 