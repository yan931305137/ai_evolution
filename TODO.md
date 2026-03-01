
# Project Tasks(要求工作内容用中文描述)

## High Priority
- [x] **[PO]** Create PRD for autonomous memory consolidation features (dreaming)
- [x] **[Design]** Design CLI dashboard for real-time agent monitoring
- [x] **[Dev]** Implement `manage_todo` integration in `AutoAgent` main loop
- [ ] **[Dev]** Replace `SimpleEmbeddingFunction` in `src/storage/memory.py` with a real local embedding model (e.g., BGE-M3, all-MiniLM-L6-v2) to improve semantic search quality.
- [ ] **[Security]** Enhance `src/utils/sandbox.py` to use AST-based static analysis instead of regex for better security check.
- [ ] **[Security]** Implement Docker-based sandbox for non-Linux environments to ensure isolation parity.

## Medium Priority
- [ ] **[Dev]** Add unit tests for `interaction_tools.py`
- [ ] **[Dev]** Refactor `src/storage/memory.py` to support multi-modal embeddings (store image/video vectors)
- [ ] **[Dev]** Implement automatic documentation generation for dynamically created agents in `src/agents/dynamic/`.
- [ ] **[Dev]** Improve error handling in `LLMClient` to better handle API rate limits and timeouts with exponential backoff (partially implemented).

## Backlog
- [ ] **[PO]** Explore integration with external knowledge bases (Wikipedia/StackOverflow)
- [ ] **[Design]** Create a web-based control panel for the agent (currently CLI only)
- [ ] **[Feature]** Implement "Sleep Mode" where the agent processes backlog tasks during low-activity periods.
