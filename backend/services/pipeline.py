from infrastructure.config import Settings, settings
from models.documents import GraphState, PipelineResult
from services.document_loader import load_requirement_documents
from services.retrieval import build_retriever, format_retrieved_documents


class RequirementEngineeringPipeline:
    """Retrieve local healthcare evidence and generate results through Kaggle Qwen."""

    def __init__(self, app_settings: Settings = settings, llm=None):
        self.settings = app_settings
        documents = load_requirement_documents(app_settings.document_directory)
        self.retriever = build_retriever(documents, app_settings)
        self.llm = llm or __import__(
            "models.llm", fromlist=["build_lightweight_llm"]
        ).build_lightweight_llm(app_settings)
        self.graph = self._build_graph()

    def _build_graph(self):
        from langgraph.graph import END, START, StateGraph

        builder = StateGraph(GraphState)
        builder.add_node("retriever", self._retrieve_node)
        builder.add_node("prd_generator", self._prd_node)
        builder.add_node("sdlc_selector", self._sdlc_node)
        builder.add_edge(START, "retriever")
        builder.add_edge("retriever", "prd_generator")
        builder.add_edge("prd_generator", "sdlc_selector")
        builder.add_edge("sdlc_selector", END)
        return builder.compile()

    def _retrieve_node(self, state: GraphState) -> dict:
        documents = self.retriever.invoke(state["user_requirement"])
        return {
            "retrieved_context": format_retrieved_documents(documents),
            "retrieved_documents": [
                {
                    "source": document.source,
                    "page": document.page,
                    "text": document.text,
                }
                for document in documents
            ],
        }

    def _prd_node(self, state: GraphState) -> dict:
        from agents.requirement_agent import generate_requirement_specification

        return {
            "prd_spec": generate_requirement_specification(
                state["user_requirement"],
                state["retrieved_context"],
                self.llm,
                app_settings=self.settings,
            )
        }

    def _sdlc_node(self, state: GraphState) -> dict:
        from agents.sdlc_agent import select_sdlc_model

        return {
            "sdlc_recommendation": select_sdlc_model(
                state["prd_spec"],
                self.llm,
                max_new_tokens=self.settings.sdlc_recommendation_tokens,
                max_time=self.settings.sdlc_generation_max_seconds,
            )
        }

    def run(self, user_requirement: str) -> PipelineResult:
        state = self.graph.invoke(
            {
                "user_requirement": user_requirement,
                "retrieved_context": "",
                "retrieved_documents": [],
                "prd_spec": "",
                "sdlc_recommendation": "",
            }
        )
        return PipelineResult(
            user_requirement=user_requirement,
            retrieved_documents=state["retrieved_documents"],
            requirement_specification=state["prd_spec"],
            sdlc_recommendation=state["sdlc_recommendation"],
        )
