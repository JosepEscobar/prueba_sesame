import json
from unittest.mock import MagicMock, patch

import pytest

from app.agents.operations_agent import OperationsAgent


class MockResponse:
    """Clase para simular la respuesta de un LLM."""
    def __init__(self, content: str):
        self.content = content


class TestOperationsAgent:
    """Pruebas para el OperationsAgent."""

    @pytest.fixture
    def operations_agent(self):
        """Fixture para el OperationsAgent con LLM simulado."""
        agent = OperationsAgent(name="operations_agent")
        # Reemplazar el LLM con un mock
        agent.llm = MagicMock()
        return agent

    def test_execute_impl_process_optimization(self, operations_agent):
        """Prueba que el agente genera recomendaciones de optimización de procesos."""
        # Configurar el mock para devolver recomendaciones
        operations_agent.llm.invoke.return_value = MockResponse(
            "Para optimizar el proceso de producción, recomiendo implementar un sistema Kanban y reducir el tiempo de setup en un 15%."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "¿Cómo podemos optimizar nuestro proceso de producción?",
            "context": {
                "current_process": "Manufactura en línea",
                "bottlenecks": ["setup time", "quality control"],
                "resources": {
                    "staff": 25,
                    "machines": 8
                }
            }
        }
        
        # Ejecutar el agente
        result = operations_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert result["confidence"] > 0.7

    def test_execute_impl_resource_allocation(self, operations_agent):
        """Prueba que el agente realiza recomendaciones de asignación de recursos."""
        # Configurar el mock para devolver recomendaciones
        operations_agent.llm.invoke.return_value = MockResponse(
            "Basado en las proyecciones, recomiendo reasignar 3 personas del departamento A al B y aumentar la inversión en equipamiento un 10%."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "¿Cómo deberíamos asignar nuestros recursos para el próximo trimestre?",
            "context": {
                "departments": ["A", "B", "C"],
                "current_allocation": {
                    "A": {"staff": 10, "budget": 50000},
                    "B": {"staff": 15, "budget": 75000},
                    "C": {"staff": 8, "budget": 40000}
                },
                "projections": {
                    "A": {"growth": -5},
                    "B": {"growth": 15},
                    "C": {"growth": 2}
                }
            }
        }
        
        # Ejecutar el agente
        result = operations_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result

    def test_execute_impl_supply_chain_analysis(self, operations_agent):
        """Prueba que el agente analiza correctamente problemas de cadena de suministro."""
        # Configurar el mock para devolver un análisis
        operations_agent.llm.invoke.return_value = MockResponse(
            "El análisis indica que el principal punto débil en la cadena de suministro es el proveedor B. Recomiendo diversificar esta fuente."
        )
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza los problemas en nuestra cadena de suministro",
            "context": {
                "suppliers": ["A", "B", "C", "D"],
                "delivery_times": {
                    "A": 5,
                    "B": 12,
                    "C": 7,
                    "D": 6
                },
                "quality_issues": {
                    "A": 2,
                    "B": 8,
                    "C": 1,
                    "D": 3
                }
            }
        }
        
        # Ejecutar el agente
        result = operations_agent._execute_impl(input_data)
        
        # Verificar el resultado
        assert "result" in result
        assert "confidence" in result
        assert result["confidence"] > 0.7

    def test_execute_impl_error_handling(self, operations_agent):
        """Prueba que el agente maneja correctamente errores y entradas incompletas."""
        # Simular error en el LLM
        operations_agent.llm.invoke.side_effect = Exception("Error simulado en LLM")
        
        # Datos de entrada para prueba
        input_data = {
            "query": "Analiza nuestras operaciones",
            "context": {}
        }
        
        # Ejecutar el agente - debería manejar la excepción y retornar algo razonable
        result = operations_agent._execute_impl(input_data)
        
        # Verificar que hay un resultado a pesar del error
        assert "result" in result or "error" in result
        assert "confidence" in result
        # La confianza debería ser baja debido al error
        assert result["confidence"] < 0.5 