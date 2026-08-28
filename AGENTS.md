# Repository instructions

- Preserve semantic scopes: `target_company`, `neutral_engineering_need`, `dspace_portfolio`.
- Do not introduce generic cross-scope `product_*` fields.
- Keep scores, mapping decisions, evidence extraction, and persistence deterministic.
- The local LLM is presentation-only and receives one summary attempt per company run.
- Add tests and record deviations in `docs/IMPLEMENTATION_NOTES.md`.
- Treat `docs/BD_AGENT_NNC_IMPLEMENTATION_SPEC.md` as authoritative for Tiny-AI,
  Edge-AI, microcontroller, neural-network, and Neural Net Coder semantics.
- Generic AI/ML evidence never passes the neural-network gate by itself.
- Every positive recommendation terminates at `neural_net_coder` and requires
  authoritative Neural Net Coder chunks from ChromaDB.
