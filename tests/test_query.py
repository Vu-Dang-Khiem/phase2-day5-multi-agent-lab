"""Integration tests using the 4 prompts from test_query.md.

Uses mocked LLM to verify routing, agent handoff, and trace output for each prompt.
"""

from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.tracing import format_trace_report
from multi_agent_research_lab.services.llm_client import LLMResponse

PATCH_LLM = "multi_agent_research_lab.services.llm_client.LLMClient.complete"

PROMPT_RESEARCH_AGENT_BENCH = """You are part of a university lab designing a benchmark to evaluate AI systems that assist students with research tasks.

Your task is to design a benchmark called ResearchAgentBench.

The benchmark should evaluate whether an AI system can actually help a graduate student complete research work, not just produce fluent text.

You must produce a full benchmark design document that includes:
1. Benchmark goal
2. Core assumptions
3. Task categories
4. At least 12 example tasks across different categories
5. A scoring rubric
6. Baselines to compare against
7. Likely failure modes and gaming risks
8. Human evaluation protocol
9. Limitations of the benchmark
10. Recommendations for version 2 of the benchmark

Constraints:
- The benchmark must be realistic for a small academic lab
- It must not depend on expensive annotation
- It must distinguish between usefulness, correctness, and research judgment
- It must include at least one adversarial or stress-test component
- It must explicitly discuss how systems might game the evaluation

Output format:
Write this as a mini design document suitable for discussion in a research lab meeting.
"""

PROMPT_MULTI_AGENT_BRIEFING = """You are helping a PhD student prepare a research briefing on the topic:

"Do multi-agent LLM systems actually outperform single-agent systems on complex tasks?"

Your task is not just to summarize the topic. You must produce a structured research briefing that:
1. Defines the main claim precisely
2. Breaks the literature into major positions or schools of thought
3. Identifies arguments supporting the claim
4. Identifies arguments challenging the claim
5. Explains where empirical evidence is weak, incomplete, or confounded
6. Distinguishes between true multi-agent gains and gains caused by other factors such as more tokens, more prompt engineering, or repeated self-reflection
7. Proposes 3 concrete experiments that could better resolve the debate
8. Ends with a balanced final judgment

Constraints:
- Do not write a generic overview
- Explicitly discuss what kinds of evidence would count as convincing
- The final judgment must include uncertainty and unresolved issues
- Organize the answer so it could be used as speaking notes for a research group meeting

Output format:
- Core question
- Main positions
- Evidence for
- Evidence against
- Methodological concerns
- Proposed experiments
- Final judgment
"""

PROMPT_EXPERIMENT_DESIGN = """You are designing a research experiment to compare a single-call LLM system with a multi-agent LLM system on complex research tasks.

Your deliverable must be a complete experimental plan.

You must include:
1. The research question
2. Hypotheses
3. Task design
4. Datasets or source materials
5. Fair comparison setup
6. Metrics
7. Human evaluation criteria
8. Statistical or methodological considerations
9. Expected results and alternative interpretations
10. A red-team section explaining how the experiment could be misleading, unfair, or easy to game
11. A revised experiment design after taking the red-team critique seriously

Constraints:
- You must explicitly address token budget fairness
- You must explain how to avoid giving the multi-agent system an unfair advantage
- You must discuss how to separate gains from decomposition vs gains from more inference time
- The red-team critique must be concrete, not superficial

Output format:
Write the answer as a structured internal lab proposal.
"""

PROMPT_SURVEY_BLUEPRINT = """You are helping prepare a survey paper titled:

"AI Agents for Research Assistance: Capabilities, Evaluation, and Open Problems"

Your task is to create a detailed survey blueprint that a graduate student could actually use to write the paper.

You must produce:
1. A proposed paper title
2. A draft abstract
3. A section-by-section outline with 6 to 8 main sections
4. For each section:
   - purpose of the section
   - key themes
   - questions the section should answer
   - likely pitfalls
   - open problems
5. A final section identifying the most important evaluation gaps in current research
6. A section explaining what a strong future benchmark should measure

Constraints:
- The sections should not overlap too much
- The outline should feel like a real survey, not a blog post
- Open problems must be specific
- The final product should be useful as a writing plan, not just a topic list
"""


def _mock_llm(*args, **kwargs) -> LLMResponse:
    return LLMResponse(
        content="Mocked research notes with key findings and citations.",
        input_tokens=50,
        output_tokens=100,
        cost_usd=0.0001,
    )


def _run_with_mocks(query: str) -> ResearchState:
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    result = workflow.run(state)
    return result


# --- Test 1: ResearchAgentBench Benchmark Design (Prompt 1 in test_query.md) ---

def test_research_agent_bench(monkeypatch) -> None:
    monkeypatch.setattr(PATCH_LLM, _mock_llm)
    result = _run_with_mocks(PROMPT_RESEARCH_AGENT_BENCH)
    assert result.final_answer is not None
    assert result.iteration >= 1
    assert "researcher" in result.route_history
    assert "writer" in result.route_history
    assert len(result.agent_results) >= 2


# --- Test 2: Multi-Agent Research Briefing (Prompt 2 in test_query.md) ---

def test_multi_agent_briefing(monkeypatch) -> None:
    monkeypatch.setattr(PATCH_LLM, _mock_llm)
    result = _run_with_mocks(PROMPT_MULTI_AGENT_BRIEFING)
    assert result.final_answer is not None
    assert result.iteration >= 2
    assert "analyst" in result.route_history


# --- Test 3: Experimental Design (Prompt 3 in test_query.md) ---

def test_experiment_design(monkeypatch) -> None:
    monkeypatch.setattr(PATCH_LLM, _mock_llm)
    result = _run_with_mocks(PROMPT_EXPERIMENT_DESIGN)
    assert result.final_answer is not None
    assert result.research_notes is not None
    assert len(result.sources) > 0


# --- Test 4: Survey Paper Blueprint (Prompt 4 in test_query.md) ---

def test_survey_blueprint(monkeypatch) -> None:
    monkeypatch.setattr(PATCH_LLM, _mock_llm)
    result = _run_with_mocks(PROMPT_SURVEY_BLUEPRINT)
    assert result.final_answer is not None
    assert result.analysis_notes is not None


# --- Extra: trace report format ---

def test_trace_report_format(monkeypatch) -> None:
    monkeypatch.setattr(PATCH_LLM, _mock_llm)
    result = _run_with_mocks(PROMPT_RESEARCH_AGENT_BENCH)
    report = format_trace_report(result)
    assert "Trace Report" in report
    assert result.request.query in report
    assert "Agent Results" in report
