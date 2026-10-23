# RAG architecture

Vue /chat or quiz AS -> owner-authenticated Spring sessions/history -> Python AnswerService.graph.invoke -> retrieve (structured query extraction, exact metadata filter, Chroma similarity/MMR, structured candidate selection) -> generate (GMS bounded JSON, citation IDs/order/numbers) -> Spring PostgreSQL answer/citation snapshots -> safe Vue Markdown/code/evidence panel.

The graph stores no cross-session conversation state. A bounded hashed query-vector cache stores embeddings only. The offline deterministic provider is explicitly reported by /chat/status; GMS without key/index does not silently substitute canned answers.

Actual graph: [execution evidence](evidence/live-probe.json). API basis: [LangGraph StateGraph reference](https://reference.langchain.com/python/langgraph/graph/state/StateGraph).
