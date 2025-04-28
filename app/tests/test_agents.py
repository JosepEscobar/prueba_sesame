import pytest
from app.agents.router_agent import RouterAgent
from app.agents.analysis_agent import AnalysisAgent
from app.agents.action_agent import ActionAgent
from app.agents.summary_agent import SummaryAgent
from app.core.graph import AgentGraph

@pytest.mark.asyncio
async def test_router_agent():
    agent = RouterAgent()
    result = await agent.execute({"query": "Analiza este texto"})
    assert "agent_decision" in result
    assert "confidence" in result
    assert result["confidence"] > 0

@pytest.mark.asyncio
async def test_analysis_agent():
    agent = AnalysisAgent()
    result = await agent.execute({"content": "Este es un texto de prueba para análisis"})
    assert "analysis" in result
    assert "confidence" in result
    assert result["confidence"] > 0

@pytest.mark.asyncio
async def test_action_agent():
    agent = ActionAgent()
    result = await agent.execute({"action_request": "Realiza una acción de prueba"})
    assert "action_result" in result
    assert "confidence" in result
    assert result["confidence"] > 0

@pytest.mark.asyncio
async def test_summary_agent():
    agent = SummaryAgent()
    result = await agent.execute({"content": "Este es un texto largo que necesita ser resumido"})
    assert "summary" in result
    assert "confidence" in result
    assert result["confidence"] > 0

@pytest.mark.asyncio
async def test_agent_graph():
    graph = AgentGraph()
    result = await graph.execute({
        "query": "Analiza este texto",
        "content": "Este es un texto de prueba para análisis"
    })
    assert "agent_output" in result
    assert "confidence" in result
    assert "current_agent" in result
    assert result["confidence"] > 0 