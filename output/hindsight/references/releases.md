# Releases

Version history for this repository (43 releases).

## v0.4.20: v0.4.20
**Published:** 2026-03-24

## What's Changed
* feat: upgrade MiniMax default model from M2.5 to M2.7 by @octo-patch in https://github.com/vectorize-io/hindsight/pull/606
* docs: add 0.4.19 release blog post, Agno and Hermes integration pages by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/608
* feat: independent versioning for integrations by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/565
* blog: Hermes Agent persistent memory by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/599
* fix: rename fact_type "assistant" to "experience" across extraction pipeline by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/609
* Fix entity_id null constraint for non-ASCII entity names by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/612
* feat: 4-tab code parity across all documentation examples by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/613
* feat: add scrolling integrations banner to all doc pages by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/616
* feat(skill): validate links, strip images, include openapi.json and changelog by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/614
* fix(security): address all Dependabot vulnerability alerts by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/617
* Fix orphaned batch_retain parents when child fails via unhandled exception by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/618
* Fix non-atomic async operation creation by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/619
* feat: fact_types and mental model exclusion filters for reflect by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/615
* feat(docs): Integrations Hub + unified page hero by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/620
* Enhance OpenAI client initialization to support Azure OpenAI deployments by @c15yi in https://github.com/vectorize-io/hindsight/pull/623
* fix(hindsight-api): add script entry points so uvx hindsight-api works directly by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/629
* feat: add LangGraph integration by @DK09876 in https://github.com/vectorize-io/hindsight/pull/610
* feat(nemoclaw): add hindsight-nemoclaw setup CLI package by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/630
* doc: add langgraph and nemoclaw by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/633
* blog: Give NemoClaw the Best Agent Memory Available In One Command by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/631
* fix: add readme field to integration pyproject.toml files for PyPI by @DK09876 in https://github.com/vectorize-io/hindsight/pull/634
* fix: MCP tool calls fail when MCP_AUTH_TOKEN and TENANT_API_KEY differ by @DK09876 in https://github.com/vectorize-io/hindsight/pull/635
* fix(litellm): fall back to last user message when hindsight_query not provided by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/641
* fix: allow claude-agent-sdk installation on Linux/Docker by @Bortlesboat in https://github.com/vectorize-io/hindsight/pull/644
* Fix: POST files/retain uses authentication headers by @soberreu in https://github.com/vectorize-io/hindsight/pull/636
* fix(recall): reject empty queries with 400 and fix SQL parameter gap by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/632
* docs: add gitcgr code graph badge by @vitali87 in https://github.com/vectorize-io/hindsight/pull/648
* fix: strip markdown code fences from all LLM providers, not just local by @feniix in https://github.com/vectorize-io/hindsight/pull/646
* feat(extensions): add context enrichment to OperationValidatorExtension by @mrkhachaturov in https://github.com/vectorize-io/hindsight/pull/639
* Fix pg_trgm unavailability causing startup crash and silent retain failures by @coder999999999 in https://github.com/vectorize-io/hindsight/pull/649
* Add wall-clock timeout to reflect operations by @ThePlenkov in https://github.com/vectorize-io/hindsight/pull/643
* test: add unit tests for pg_trgm auto-detection and ValidationResult.accept_with() enrichment by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/650
* docs: update HindClaw integration listing by @mrkhachaturov in https://github.com/vectorize-io/hindsight/pull/653
* feat: Add Claude Code integration plugin by @fabioscarsi in https://github.com/vectorize-io/hindsight/pull/651
* fix(claude-code): fix plugin installation, config UX, and release workflow by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/661
* doc: Claude Code + Telegram + Hindsight blog post by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/656
* fix(entity_resolver): prevent _pending_stats/_pending_cooccurrences memory leak by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/662
* fix(claude-code): pre-start daemon in background on SessionStart by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/663
* feat(blog): Agent Memory Benchmark launch post by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/657
* blog: add cover images to AMB, Claude Code Telegram, and NemoClaw posts by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/667
* chore(deps): bump actions/setup-python from 5 to 6 by @dependabot[bot] in https://github.com/vectorize-io/hindsight/pull/654
* fix(reflect): disable source facts in search_observations to prevent context overflow by @kagura-agent in https://github.com/vectorize-io/hindsight/pull/669

## New Contributors
* @c15yi made their first contribution in https://github.com/vectorize-io/hindsight/pull/623
* @Bortlesboat made their first contribution in https://github.com/vectorize-io/hindsight/pull/644
* @soberreu made their first contribution in https://github.com/vectorize-io/hindsight/pull/636
* @vitali87 made their first contribution in https://github.com/vectorize-io/hindsight/pull/648
* @feniix made their first contribution in https://github.com/vectorize-io/hindsight/pull/646
* @mrkhachaturov made their first contribution in https://github.com/vectorize-io/hindsight/pull/639
* @coder999999999 made their first contribution in https://github.com/vectorize-io/hindsight/pull/649
* @ThePlenkov made their first contribution in https://github.com/vectorize-io/hindsight/pull/643
* @kagura-agent made their first contribution in https://github.com/vectorize-io/hindsight/pull/669

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.19...v0.4.20

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.20)

---

## v0.4.19: v0.4.19
**Published:** 2026-03-18

## What's Changed
* doc: add 0.4.18 release blog post by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/567
* fix: support for gemini-3.1-flash-lite-preview (thought_signature in tool calls) by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/568
* docs: improve type hints and documentation in client_wrapper by @hiSandog in https://github.com/vectorize-io/hindsight/pull/570
* fix: inject Accept header in MCP middleware to prevent 406 errors by @DK09876 in https://github.com/vectorize-io/hindsight/pull/571
* blog: add disposition-aware agents post by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/566
* Upgrade GitHub Actions to latest versions by @salmanmkc in https://github.com/vectorize-io/hindsight/pull/576
* chore(deps): bump actions/setup-python from 5 to 6 by @dependabot[bot] in https://github.com/vectorize-io/hindsight/pull/583
* chore(deps): bump actions/download-artifact from 4 to 8 by @dependabot[bot] in https://github.com/vectorize-io/hindsight/pull/582
* chore(deps): bump actions/checkout from 4 to 6 by @dependabot[bot] in https://github.com/vectorize-io/hindsight/pull/581
* fix: chunk FK cascade so doc deletion doesn't leave orphan memory units by @jnMetaCode in https://github.com/vectorize-io/hindsight/pull/580
* fix(migration): backsweep orphaned observation memory units by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/584
* feat: local reranker FP16, bucket batching, and transformers 5.x compatibility by @fabioscarsi in https://github.com/vectorize-io/hindsight/pull/588
* fix(docker): honor HINDSIGHT_CP_HOSTNAME for control-plane startup by @abix5 in https://github.com/vectorize-io/hindsight/pull/590
* docs: add config vars for local reranker FP16 and bucket batching by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/589
* docs(skills): encourage rich context over pre-summarized strings in retain by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/594
* blog: add n8n persistent memory workflows post by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/585
* docs: add Best Practices unversioned page by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/598
* feat: hindsight-hermes integration for Hermes Agent by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/600
* feat(retain): verbatim, chunks modes and named retain strategies by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/593
* blog: Streamlit chatbot with persistent memory by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/602
* fix: prevent silent memory loss on consolidation LLM failure by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/601
* blog: fix streamlit post slug and add cover image by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/604
* blog: fix internal links in streamlit post by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/605
* feat: add Agno integration with Hindsight memory toolkit by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/596
* feat(typescript-client): Deno compatibility by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/607

## New Contributors
* @hiSandog made their first contribution in https://github.com/vectorize-io/hindsight/pull/570
* @jnMetaCode made their first contribution in https://github.com/vectorize-io/hindsight/pull/580

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.18...v0.4.19

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.19)

---

## v0.4.18: v0.4.18
**Published:** 2026-03-13

## What's Changed
* doc: add 0.4.17 release blog post by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/538
* perf: replace window-function retrieval with UNION ALL + per-bank HNSW indexes by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/541
* feat: make recall max query tokens configurable via env var by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/544
* feat: add jina-mlx reranker provider for Apple Silicon by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/542
* doc: Run Hindsight with Ollama: Local AI Memory, No API Keys Needed by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/536
* doc: What's New in Hindsight Cloud — Programmatic API Key Management by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/543
* fix: cancel in-flight async ops when bank is deleted by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/545
* fix: register embedded profiles in CLI metadata on daemon start by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/546
* fix(openclaw): keep recalled memories out of the visible transcript by @stablegenius49 in https://github.com/vectorize-io/hindsight/pull/548
* blog: Time-Aware Spreading Activation for Memory Graphs by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/547
* feat: add MiniMax LLM provider support by @octo-patch in https://github.com/vectorize-io/hindsight/pull/550
* fix: truncate documents exceeding LiteLLM reranker context limit by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/549
* Upgrade GitHub Actions to latest versions by @salmanmkc in https://github.com/vectorize-io/hindsight/pull/553
* chore: add dependabot config for GitHub Actions updates by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/554
* chore(deps): bump actions/cache from 4 to 5 by @dependabot[bot] in https://github.com/vectorize-io/hindsight/pull/559
* chore(deps): bump actions/setup-go from 5 to 6 by @dependabot[bot] in https://github.com/vectorize-io/hindsight/pull/558
* chore(deps): bump actions/upload-artifact from 4 to 7 by @dependabot[bot] in https://github.com/vectorize-io/hindsight/pull/555
* chore(deps): bump actions/checkout from 4 to 6 by @dependabot[bot] in https://github.com/vectorize-io/hindsight/pull/556
* feat: introduce hindsight-api-slim and hindsight-all-slim packages by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/560
* fix: remove broken minimax test and enhance slim smoke tests by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/564
* chore(deps): bump actions/setup-node from 4 to 6 by @dependabot[bot] in https://github.com/vectorize-io/hindsight/pull/557
* docs: revamp sidebar with icon grids and language support by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/563
* feat: compound tag filtering via tag_groups by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/562

## New Contributors
* @stablegenius49 made their first contribution in https://github.com/vectorize-io/hindsight/pull/548
* @octo-patch made their first contribution in https://github.com/vectorize-io/hindsight/pull/550
* @salmanmkc made their first contribution in https://github.com/vectorize-io/hindsight/pull/553
* @dependabot[bot] made their first contribution in https://github.com/vectorize-io/hindsight/pull/559

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.17...v0.4.18

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.18)

---

## v0.4.17: v0.4.17
**Published:** 2026-03-10

## What's Changed
* doc: add 0.4.16 release blog post and changelog by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/502
* fix: truncate long bank names in selector dropdown by @dcbouius in https://github.com/vectorize-io/hindsight/pull/505
* fix: refresh bank list when dropdown is opened by @dcbouius in https://github.com/vectorize-io/hindsight/pull/504
* fix: openclaw tests + split doc-examples CI per language by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/503
* doc: document all missing bank config fields in memory-banks.mdx by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/508
* Add on_file_convert_complete extension hook after file-to-markdown conversion by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/507
* feat: add source facts token limits to consolidation and recall by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/509
* refactor: remove dead code and clarify observations vs mental models by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/512
* feat: per-request file parser selection with fallback chains by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/514
* feat: observation history tracking and diff UI by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/513
* feat: mental model history tracking and UI diff view by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/516
* doc: Upgrading OpenClaw's Memory with Hindsight by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/515
* Fix GCS auth for Workload Identity Federation credentials by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/518
* feat: change tags for a document by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/517
* fix: serialize Alembic upgrades in-process by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/521
* Fix Iris parser httpx read timeout by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/524
* fix: migrate mental_models.embedding dimension alongside memory_units by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/526
* feat: filter operations by type + fix stale auto-refresh closure (#522) by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/527
* fix(consolidation): respect bank mission over ephemeral-state heuristic by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/525
* docs: add FAQ entry for conversation retain format by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/529
* fix: normalize named tool_choice to avoid HTTP 400 on LM Studio / Ollama by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/528
* doc: Your Pydantic AI Agent Forgets You After Every Run. Fix It in 5 Lines. by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/531
* Fix run-db-migration for all-tenant upgrades by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/530
* doc: What's New in Hindsight — Document File Upload by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/532
* doc: split blog index into Hindsight and Hindsight Cloud sections by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/534
* fix: strip null bytes from parsed file content before retain by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/535
* fix: resolve remaining webhook schema issues in multi-tenant retain by @Andreymi in https://github.com/vectorize-io/hindsight/pull/533
* feat: manual retry for failed async operations by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/537


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.16...v0.4.17

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.17)

---

## v0.4.16: v0.4.16
**Published:** 2026-03-05

## What's Changed
* docs: 0.4.15 release blog post and changelog by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/477
* doc: update cookbook by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/479
* blog: add LiteLLM persistent memory post by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/481
* doc: fix LiteLLM blog — OPINION → OBSERVATION, update title by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/482
* cli: add linux-arm64 binary to release and CI by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/484
* fix: resolve all Dependabot security vulnerabilities by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/486
* doc: add ZeroEntropy reranker to models.md by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/489
* feat: webhook system with retain.completed event, UI, and docs by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/487
* fix: resolve TypeError when LLM returns invalid JSON across all retries by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/490
* Fix bank-level MCP tool filtering for FastMCP 3.x by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/491
* doc: add MCP blog post by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/492
* perf: add GIN index on source_memory_ids for observation lookup by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/485
* fix: replace additive combined scoring with multiplicative CE boosts by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/494
* fix: cap uvicorn graceful shutdown at 5s and enable force-kill on double Ctrl+C by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/495
* fix: resolve chunks for observation results via source_memory_ids by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/496
* feat(openclaw): v2 recall/retention controls, scalability fixes, and Gemini safety settings by @mysteriousHerb in https://github.com/vectorize-io/hindsight/pull/480
* fix: use correct schema name in webhook outbox callback by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/499
* fix: run schema migrations in thread to prevent event loop deadlock by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/500
* doc: Give Your OpenAI App a Memory in 5 Minutes by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/498
* fix: preserve None temporal fields for observations without source dates by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/501

## New Contributors
* @mysteriousHerb made their first contribution in https://github.com/vectorize-io/hindsight/pull/480

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.15...v0.4.16

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.16)

---

## v0.4.15: v0.4.15
**Published:** 2026-03-03

## What's Changed
* doc: changelog and blog post by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/445
* doc: improvements by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/448
* doc: 0.4.14 by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/449
* feat: observation_scopes field to drive observations granularity by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/447
* feat(openclaw): retain last n+2 turns every n turns (default n=10) by @fabioscarsi in https://github.com/vectorize-io/hindsight/pull/452
* Add bank-scoped validation to engine and HTTP handlers by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/454
* fix: JSON serialization and logging exception propagation in claude_code_llm by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/461
* fix: zeroentropy rerank URL missing /v1 prefix and MCP retain async_processing param by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/460
* fix(control-plane): observations count always showing 0 by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/464
* fix: resolve consolidation deadlock caused by zombie processing tasks on retry by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/463
* fix(reflect): prevent context_length_exceeded on large memory banks by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/462
* feat: support timestamp="unset" to retain content without a date by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/465
* feat: entity labels — optional, free_values, multi_value, UI polish by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/450
* docs: entities vs tags vs metadata by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/466
* feat: add Pydantic AI integration for persistent agent memory by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/441
* feat: add Pydantic AI integration to CI, release pipeline, and docs by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/467
* feat: add tags filtering and q description fix for list documents API by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/468
* blog: add CrewAI persistent memory post by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/471
* feat: add extension hooks for root routing and error headers by @DK09876 in https://github.com/vectorize-io/hindsight/pull/470
* refactor(openclaw): replace console.log with debug() helper by @slayoffer in https://github.com/vectorize-io/hindsight/pull/456
* fix(performance): improve recall and retain performance on large banks by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/469
* feat: configurable Gemini/Vertex AI safety settings by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/473
* perf(recall): improve single-query chunk fetch by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/475
* fix(ts-sdk): send null instead of undefined when includeEntities is false by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/476
* refactor: replace set_gemini_safety_settings() with LLMProvider.with_config() by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/474

## New Contributors
* @fabioscarsi made their first contribution in https://github.com/vectorize-io/hindsight/pull/452

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.14...v0.4.15

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.15)

---

## v0.4.14: v0.4.14
**Published:** 2026-02-26

## What's Changed
* doc: 0.4.13 changelog by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/411
* fix(chore): include hindsight-crewai in release workflow by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/412
* feat(openclaw): add autoRecall toggle and excludeProviders schema by @slayoffer in https://github.com/vectorize-io/hindsight/pull/413
* doc: improve api explanation by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/415
* misc: fix vertex/gemini errors and use it for ci tests by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/414
* Fix bank config API for multi-tenant schema isolation by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/417
* feat: add ZeroEntropy reranker provider support by @franchb in https://github.com/vectorize-io/hindsight/pull/420
* Fix reflect based_on population and enforce full hierarchical retrieval by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/421
* fix: improve memory footprint of recall by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/423
* feat: include doc metadata in fact extraction by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/424
* feat: increase customization for reflect, retain and consolidation by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/419
* feat: enable bank config API by default by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/426
* feat: add reflect mode to LoComo benchmark and improve reflect agent by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/428
* fix(openclaw): pass auth token to health check endpoint by @slayoffer in https://github.com/vectorize-io/hindsight/pull/427
* fix: handle observations regeneration when memories get deleted by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/429
* feat: batch observations consolidation by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/430
* feat: expand MCP tool surface area by @DK09876 in https://github.com/vectorize-io/hindsight/pull/435
* feat: filter graph memories with tags by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/431
* fix: pass encoding_format="float" in LiteLLM SDK embedding calls by @franchb in https://github.com/vectorize-io/hindsight/pull/434
* fix: catch ValueError instead of bare except in date parsing by @haosenwang1018 in https://github.com/vectorize-io/hindsight/pull/438
* feat: configure exposed mcp tools per bank by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/439
* fix(storage): use dynamic schema_getter in PostgreSQLFileStorage for multi-tenant by @Andreymi in https://github.com/vectorize-io/hindsight/pull/440
* fix: fail fast HNSW index when embedding dimension exceeds 2000 by @slayoffer in https://github.com/vectorize-io/hindsight/pull/361
* feat: add Chat SDK integration for persistent chat bot memory by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/442
* chore: integrate chat with release by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/443
* fix: doc build and add chat doc by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/444

## New Contributors
* @haosenwang1018 made their first contribution in https://github.com/vectorize-io/hindsight/pull/438
* @Andreymi made their first contribution in https://github.com/vectorize-io/hindsight/pull/440

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.13...v0.4.14

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.14)

---

## v0.4.13: v0.4.13
**Published:** 2026-02-19

## What's Changed
* doc: changelog for 0.4.12 by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/397
* fix: document not tracked if has 0 extracted facts by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/399
* feat: add CrewAI integration for persistent crew memory by @benfrank241 in https://github.com/vectorize-io/hindsight/pull/319
* fix: clients don't respect timeout setting by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/400
* fix: reduce temporal ordering offset from 10s to 10ms by @dcbouius in https://github.com/vectorize-io/hindsight/pull/402
* fix: reranker crashes on provider error by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/403
* fix(mcp): stateless param not supported anymore by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/406
* feat: include source facts in observation recall by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/404
* fix: docker startup fails with named docker volumes by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/405
* fix(mcp): unify hindsight-mcp-local and server mcp  by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/407
* fix: npx hindsight-control-plane fails by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/408
* feat: switch default model to gpt-4o-mini by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/410

## New Contributors
* @benfrank241 made their first contribution in https://github.com/vectorize-io/hindsight/pull/319

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.12...v0.4.13

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.13)

---

## v0.4.12: v0.4.12
**Published:** 2026-02-18

## What's Changed
* doc: changelog and blog post for 0.4.11 by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/363
* feat: allow chunks-only in recall (max_tokens=0) by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/364
* fix(openclaw): remove unused imports, retry health check, suppress unhandled rejection by @slayoffer in https://github.com/vectorize-io/hindsight/pull/373
* fix: propagate document_tags in async retain path by @abix5 in https://github.com/vectorize-io/hindsight/pull/374
* feat: add Go client SDK with ogen code generation by @franchb in https://github.com/vectorize-io/hindsight/pull/375
* fix: improve async batch retain with large payloads by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/366
* feat: support Batch API for retain (openai/groq) by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/365
* feat: use official go generator for Go client by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/377
* feat: support for pgvectorscale (DiskANN) by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/378
* doc: add go client examples by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/380
* ci: ensure docs get created with no extracted facts by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/379
* feat: support azure pg_diskann by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/381
* doc: add faq page by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/383
* fix(openclaw): error E2BIG on large content ingested by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/389
* fix(python-client): async method parity and server keepalive timeout by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/387
* feat: accept pdf, images and office files by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/390
* fix: restore entity retrieval in recall by @dcbouius in https://github.com/vectorize-io/hindsight/pull/391
* fix(go-client): use monorepo-compatible module path by @franchb in https://github.com/vectorize-io/hindsight/pull/392
* feat: improve ai sdk tools by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/394
* fix(go-client): add go build to CI by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/393
* fix(openclaw): shell safety, HTTP dual-mode, lazy reinit, per-user banks by @slayoffer in https://github.com/vectorize-io/hindsight/pull/388
* feat: add iris as file parser by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/395
* fix: improve openclaw test coverage by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/396

## New Contributors
* @abix5 made their first contribution in https://github.com/vectorize-io/hindsight/pull/374
* @franchb made their first contribution in https://github.com/vectorize-io/hindsight/pull/375

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.11...v0.4.12

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.12)

---

## v0.4.11: v0.4.11
**Published:** 2026-02-13

## What's Changed
* fix(helm): gke overriding HINDSIGHT_API_PORT by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/328
* feat(helm): add PDB and per-component affinity support by @nuclon in https://github.com/vectorize-io/hindsight/pull/327
* feat(openclaw): add excludeProviders config by @GodsBoy in https://github.com/vectorize-io/hindsight/pull/332
* Fix MCP usage metering: propagate tenant_id through context vars by @DK09876 in https://github.com/vectorize-io/hindsight/pull/334
* feat: add otel traceability by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/330
* feat: add docs skill by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/335
* fix: include tiktoken in slim image by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/336
* Fix async batch retain incorrectly marked as internal by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/338
* feat: add mental model CRUD tools to MCP server by @DK09876 in https://github.com/vectorize-io/hindsight/pull/337
* feat(helm): add TEI reranker sidecar support by @slayoffer in https://github.com/vectorize-io/hindsight/pull/333
* Harden MCP server: fix routing, validation, and usage metering by @DK09876 in https://github.com/vectorize-io/hindsight/pull/341
* Add actual LLM token usage fields to RetainResult by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/342
* fix: improve model configuration for litellm gateway by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/345
* fix: add trust_code env config by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/347
* Replace waitlist links with direct signup URL by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/349
* Fix MCP extra args rejection and bank ID resolution priority by @DK09876 in https://github.com/vectorize-io/hindsight/pull/351
* feat: add reverse proxy support by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/346
* Implement the vchord / pgvector support by @qdrddr in https://github.com/vectorize-io/hindsight/pull/350
* fix: resolve based_on schema/serialization issues in reflect API  by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/348
* feat: implement hierarchical configuration (system, tenant, bank) by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/329
* feat: support for other text and vector search pg extensions by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/355
* chore: remove dead code by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/356
* Fix incorrect MCP tool parameters in docs by @DK09876 in https://github.com/vectorize-io/hindsight/pull/358
* feat: support timescale pg_textsearch as text search extension by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/359
* feat: support litellm-sdk as reranker and embeddings by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/357
* fix(openclaw): avoid memory retain recursion by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/362

## New Contributors
* @qdrddr made their first contribution in https://github.com/vectorize-io/hindsight/pull/350

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.10...v0.4.11

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.11)

---

## v0.4.10: v0.4.10
**Published:** 2026-02-09

## What's Changed
* fixed cast error by @haydenrear in https://github.com/vectorize-io/hindsight/pull/300
* fix: tagged directives should be applied to tagged mental models by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/303
* docs: add AI SDK integration documentation by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/304
* ci: ensure backwards/forward compatibility of the API by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/306
* fix(openclaw): remove format:uri to fix ajv warning by @GodsBoy in https://github.com/vectorize-io/hindsight/pull/309
* feat: support markdown in reflect and mental models by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/307
* ci: ensure python 3.14 compatibility by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/310
* fix(ci): resolve flaky test failures in api tests by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/311
* feat: slim docker distro by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/314
* doc: update claude-code usage terms by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/315
* fix: hindsight-embed profiles are not loaded correctly by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/316
* feat: add TenantExtension auth to MCP endpoint by @DK09876 in https://github.com/vectorize-io/hindsight/pull/286
* doc: improve Node.js client example by @vanvuongngo in https://github.com/vectorize-io/hindsight/pull/320
* feat: improve mcp tools based on endpoint by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/318
* fix(openclaw): prevent memory wipe on every session by @slayoffer in https://github.com/vectorize-io/hindsight/pull/323
* feat: add docker-compose example by @vanvuongngo in https://github.com/vectorize-io/hindsight/pull/313
* fix: do not log db user/password by @vanvuongngo in https://github.com/vectorize-io/hindsight/pull/312
* Add Supabase tenant extension by @jerryhenley in https://github.com/vectorize-io/hindsight/pull/267
* fix(helm): improve appVersion usage by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/326
* doc: prepare doc for 0.4.10 by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/325

## New Contributors
* @haydenrear made their first contribution in https://github.com/vectorize-io/hindsight/pull/300
* @vanvuongngo made their first contribution in https://github.com/vectorize-io/hindsight/pull/320
* @jerryhenley made their first contribution in https://github.com/vectorize-io/hindsight/pull/267

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.9...v0.4.10

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.10)

---

## v0.4.9: v0.4.9
**Published:** 2026-02-04

## What's Changed
* doc: changelog for 0.4.8 by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/283
* doc: update cookbook by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/284
* fix(openclaw): improve shell argument escaping by @slayoffer in https://github.com/vectorize-io/hindsight/pull/288
* feat(openclaw): add external Hindsight API support by @slayoffer in https://github.com/vectorize-io/hindsight/pull/289
* docs: expand external API configuration for OpenClaw by @slayoffer in https://github.com/vectorize-io/hindsight/pull/294
* feat(openclaw): add dynamic per-channel memory banks by @slayoffer in https://github.com/vectorize-io/hindsight/pull/290
* fix: hide hf logging by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/295
* fix: improve claude code and codex for /reflect by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/285
* feat(hindsight-litellm): support streaming on wrappers by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/296
* feat: HindsightEmbedded python SDK by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/293
* feat: improve mental models ux on control plane by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/297
* Fix recall endpoint timeout handling and add query length validation by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/298
* feat: ai sdk integration by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/299


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.8...v0.4.9

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.9)

---

## v0.4.8: v0.4.8
**Published:** 2026-02-03

## What's Changed
* Add pre-operation validation hooks for mental model create/refresh by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/271
* Propagate request context through async task payloads by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/273
* feat(openclaw): add llmProvider/llmModel plugin config options by @GodsBoy in https://github.com/vectorize-io/hindsight/pull/274
* feat: print version during startup by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/275
* feat: support for codex and claude-code as llm by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/276
* feat(embed): add hindisght-embed profiles by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/277
* fix: custom pg schema is not reliable by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/278
* Fix: load operation validator extension in worker by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/280
* feat: improve openclaw and hindisght-embed params by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/279
* fix(sec): upgrade vulnerable deps by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/254
* fix: improve embed ux with rich logging and profile isolation by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/282


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.7...v0.4.8

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.8)

---

## v0.4.7: v0.4.7
**Published:** 2026-01-31

## What's Changed
* fix: worker doesn't pick up correct default schema by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/259
* fix: sanitize null bytes from text fields before PostgreSQL insertion by @slayoffer in https://github.com/vectorize-io/hindsight/pull/238
* feat(docker): preload tiktoken encoding during build by @slayoffer in https://github.com/vectorize-io/hindsight/pull/249
* fix(hindsight-embed): respect HINDSIGHT_API_DATABASE_URL if already set by @GodsBoy in https://github.com/vectorize-io/hindsight/pull/262
* Add extension hooks for mental model operations by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/260
* feat(hindsight-embed): external API support + OpenClaw fixes (#263, #264) by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/265

## New Contributors
* @GodsBoy made their first contribution in https://github.com/vectorize-io/hindsight/pull/262

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.6...v0.4.7

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.7)

---

## v0.4.6: v0.4.6
**Published:** 2026-01-30

## What's Changed
* fix: openclaw binds embed versioning by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/256
* doc: show embed page by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/255
* fix: openclaw improve config setup by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/258


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.5...v0.4.6

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.6)

---

## v0.4.5: v0.4.5
**Published:** 2026-01-30

## What's Changed
* fix: retain async with timestamp might fails by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/253


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.4...v0.4.5

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.5)

---

## v0.4.4: v0.4.4
**Published:** 2026-01-30

## What's Changed
* fix: retain async fails if timestamp is set by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/251
* fix: rename openclawd to openclaw by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/252


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.3...v0.4.4

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.4)

---

## v0.4.3: v0.4.3
**Published:** 2026-01-30

## What's Changed
* fix: pass tenant extension to worker MemoryEngine for correct schema context by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/236
* fix: run migrations on tenant schemas at startup and harden worker poller by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/237
* feat: support vertex as llm provider by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/233
* Switch Vertex AI provider to native genai SDK by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/242
* fix(control-plane): handle undefined response.data in graph route by @slayoffer in https://github.com/vectorize-io/hindsight/pull/239
* feat(cli): add --wait flag for consolidate and --date filter for document list by @slayoffer in https://github.com/vectorize-io/hindsight/pull/244
* fix(control-plane): pass API key to dataplane for tenant auth by @slayoffer in https://github.com/vectorize-io/hindsight/pull/243
* fix(auth): skip tenant auth for all internal background tasks by @slayoffer in https://github.com/vectorize-io/hindsight/pull/240
* feat(mcp): add Bearer token authentication and tenant auth propagation by @slayoffer in https://github.com/vectorize-io/hindsight/pull/241
* chore: remove dead code by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/245
* fix: improve doc on vertexai and mcp by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/247
* fix(docker): add retry logic for ML model downloads by @slayoffer in https://github.com/vectorize-io/hindsight/pull/248
* fix: rename moltbot to openclawd by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/246
* fix: deadlock in worker polling by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/250


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.2...v0.4.3

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.3)

---

## v0.4.2: v0.4.2
**Published:** 2026-01-29

## What's Changed
* fix(doc): improve docs versioning and release by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/231
* fix: hindsight-embed on macos crashes by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/228
* feat: moltbot integration by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/216
* feat: add real-time timing breakdown logging for consolidation by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/235
* feat: add more config options for llm retries by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/234


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.1...v0.4.2

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.2)

---

## v0.4.1: v0.4.1
**Published:** 2026-01-29

## What's Changed
* doc: add blog by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/201
* doc: release notes for 0.4.0 by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/217
* fix: include correct __version__ in python packages by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/218
* doc: improve readme by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/223
* feat: support different default pg schema by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/222
* fix: add defensive error handling to PyTorch device detection by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/221
* fix: search_mental_models uuid type mismatch by @DK09876 in https://github.com/vectorize-io/hindsight/pull/225
* fix: /version endpoint return wrong version by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/224
* doc: hide next version by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/226
* feat: consolidation performance benchmark and optimization by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/227


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.4.0...v0.4.1

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.1)

---

## v0.4.0: v0.4.0
**Published:** 2026-01-28

## What's Changed
* doc: changelog for 0.3.0 by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/156
* doc: update expired Slack invite link by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/157
* feat: add cloud mode to skill installer for team memory sharing by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/158
* Fix skill installer test examples to use meaningful content by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/160
* feat(cli): accept more file types on retain-files by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/163
* feat: introduce mental models by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/132
* doc: refinement for 0.3.0 new features by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/159
* Add structured JSON logging support by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/170
* feat: improve mental model refresh and add directives by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/166
* chore: unify agents.md and claude.md by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/173
* fix(sec): upgrade vulnerable deps by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/174
* feat(clients): mental models api by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/172
* fix: pytorch init failures by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/175
* feat: new 'worker' service by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/176
* chore: drop unused access_count column by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/178
* fix: improve pytorch model initialization to prevent meta tensor issues by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/180
* fix: sometimes memories gets extracted in the wrong language by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/184
* fix: simplify pytorch model initialization to prevent meta tensor issues by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/185
* feat: revisit mental models, directives and reflections by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/179
* Fix Gemini tool response format by including function name by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/187
* feat(python-sdk): add tags filtering support to high-level client by @phamgialinhlx in https://github.com/vectorize-io/hindsight/pull/186
* feat: support for npx add-skill by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/191
* feat(mcp): add timestamp to retain by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/190
* fix: improve mental model consolidation by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/197
* feat(litellm): async retain, reflect support, and API cleanup by @DK09876 in https://github.com/vectorize-io/hindsight/pull/167
* Fix: Pass api_key to Hindsight client in litellm integration by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/193
* chore: versioned docs by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/198
* doc: mental models by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/199
* ci: add upgrade tests by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/200
* fix(ui): reflections based on don't show up all contents by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/203
* feat(litellm): support tags and mission in litellm package by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/202
* chore: internal renames by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/204
* fix: include tags, created_at, proof_count in graph table_rows by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/207
* fix: multi-tenant schema context for worker task execution by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/208
* chore: drop dead code by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/210
* fix: misc fixes for observations and mental models by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/209
* chore: cleanup benchmarks runner with old flags by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/212
* feat: add custom extraction prompt by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/213
* fix: graph endpoint not showing links for observations by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/214
* fix(embed): daemon process XPC connection crash on macos by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/215


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.3.0...v0.4.0

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.4.0)

---

## v0.3.0: v0.3.0
**Published:** 2026-01-13

## What's Changed
* feat: configurable embedding dimensions + OpenAI Embeddings by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/101
* fix: groq llm with free tier doesn't work by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/102
* Fix Python SDK not sending Authorization header by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/106
* Load .env file automatically on startup by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/104
* fix: make retain max completion tokens configurable by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/109
* fix: improve causal links detection by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/111
* ci: pin rust lock version by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/112
* feat: backup/restore by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/110
* fix(security): fix qs - CVE-2025-15284 by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/113
* feat: run db migrations offline (optionally) by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/114
* feat(helm): add existingSecret support by @nuclon in https://github.com/vectorize-io/hindsight/pull/119
* feat: Add per-request LLM token usage metrics by @omototo in https://github.com/vectorize-io/hindsight/pull/117
* feat(mcp): add async_processing parameter to retain tool by @slayoffer in https://github.com/vectorize-io/hindsight/pull/95
* fix: ui shows only 1000 memories by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/121
* feat: add metrics for llm call latency by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/120
* feat: support cohere as embeddings and reranker by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/122
* feat: support for multilingual content by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/124
* fix(mcp): add back bank list and create_bank tools by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/123
* feat: support different provider/models per operation by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/125
* fix: duplicated causal relationships and token optimization by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/126
* feat: add configs for database connection by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/128
* feat: delete memory bank by @dcbouius in https://github.com/vectorize-io/hindsight/pull/127
* feat: add operation_id to retain response by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/129
* chore: add flag to not include ml libs in docker image by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/130
* ci: fix flak tests by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/131
* Fix stats endpoint missing tenant authentication by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/134
* Fix embedding dimension for tenant schemas by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/135
* fix: misc perf improvements by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/133
* feat: retain modes by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/136
* fix: improve tei client parameters by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/137
* fix(typescript-client): Add error handling to all API methods by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/139
* misc: performance improvements by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/140
* ci: frozen uv sync by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/138
* fix: improve graph retrieval on large memory banks by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/141
* fix: entities list only show 100 entities by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/142
* fix: improve mpfp retrieval by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/146
* fix: batch queries on recall by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/149
* feat: support custom url for openai embeddings & cohere by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/150
* feat: add tenant to metrics labels by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/151
* feat: support litellm gateway by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/154
* Fix: Load extensions in server.py for multi-worker deployments by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/155
* feat: add memory tags by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/152

## New Contributors
* @nuclon made their first contribution in https://github.com/vectorize-io/hindsight/pull/119
* @omototo made their first contribution in https://github.com/vectorize-io/hindsight/pull/117
* @slayoffer made their first contribution in https://github.com/vectorize-io/hindsight/pull/95

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.2.1...v0.3.0

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.3.0)

---

## v0.2.1: v0.2.1
**Published:** 2026-01-05

## What's Changed
* doc: changelog for 0.2.0 (and regenerate clients) by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/99


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.2.0...v0.2.1

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.2.1)

---

## v0.2.0: v0.2.0
**Published:** 2026-01-05

## What's Changed
* doc: add skills documentation by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/73
* Load operation validator extension in main entry point by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/72
* feat(config): Add configurable observation thresholds by @bjornslib in https://github.com/vectorize-io/hindsight/pull/83
* fix(mcp): Chain MCP lifespan with FastAPI app lifespan by @bjornslib in https://github.com/vectorize-io/hindsight/pull/81
* feat: Add Anthropic Claude and LM Studio provider support by @csfet9 in https://github.com/vectorize-io/hindsight/pull/36
* feat(doc): add new config options and supported providers by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/84
* feat: add max_tokens and structured output to /reflect by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/74
* Add operation validator extension support with proper HTTP error handling by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/86
* Feature/graph viz by @chrislatimer in https://github.com/vectorize-io/hindsight/pull/85
* feat: Add local LLM improvements for reasoning models and Docker startup by @csfet9 in https://github.com/vectorize-io/hindsight/pull/88
* feat: Add user-provided entities support to retain endpoint by @phamgialinhlx in https://github.com/vectorize-io/hindsight/pull/91
* feat(mcp): Add multi-bank access and new MCP tools by @bjornslib in https://github.com/vectorize-io/hindsight/pull/82
* misc: add mcp integration tests and increase test coverage by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/98

## New Contributors
* @bjornslib made their first contribution in https://github.com/vectorize-io/hindsight/pull/83
* @csfet9 made their first contribution in https://github.com/vectorize-io/hindsight/pull/36
* @phamgialinhlx made their first contribution in https://github.com/vectorize-io/hindsight/pull/91

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.1.16...v0.2.0

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.2.0)

---

## v0.1.16: v0.1.16
**Published:** 2025-12-23

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.1.15...v0.1.16

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.16)

---

## v0.1.15: v0.1.15
**Published:** 2025-12-23

## What's Changed
* feat(misc): update clients types, test coverage,  improve /health endpoint and add changelog by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/70
* feat: delete document from ui by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/71


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.1.14...v0.1.15

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.15)

---

## v0.1.14: v0.1.14
**Published:** 2025-12-23

## What's Changed
* fix: embed get-skill installer by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/69


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.1.13...v0.1.14

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.14)

---

## v0.1.13: v0.1.13
**Published:** 2025-12-22

## What's Changed
* fix: propagate exceptions from task handlers to enable retry logic by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/65
* feat: refactor hindsight-embed architecture by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/66
* fix(ui): timestamp is not considered in retain by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/68


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.1.12...v0.1.13

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.13)

---

## v0.1.12: v0.1.12
**Published:** 2025-12-22

## What's Changed
* fix: set max_completion_tokens to 100 in llm validation by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/59
* ci: finalize test for the documentation code by @DK09876 in https://github.com/vectorize-io/hindsight/pull/57
* Improve LLM JSON parsing error handling with retry logic and detailed logging by @cesarandreslopez in https://github.com/vectorize-io/hindsight/pull/61
* feat: extensions + astral ty checks + docs improvements by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/54
* doc: add documentation for extensions by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/62
* fix: ollama structured support by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/63
* feat: add hindsight-embed and native agentic skill by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/64

## New Contributors
* @cesarandreslopez made their first contribution in https://github.com/vectorize-io/hindsight/pull/61

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.1.11...v0.1.12

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.12)

---

## v0.1.11: v0.1.11
**Published:** 2025-12-18

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.1.10...v0.1.11

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.11)

---

## v0.1.10: v0.1.10
**Published:** 2025-12-18

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.1.9...v0.1.10

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.10)

---

## v0.1.8: v0.1.8
**Published:** 2025-12-17

## What's Changed
* Fix: bank selector race condition when switching banks (#38) by @wsimmonds in https://github.com/vectorize-io/hindsight/pull/39
* fix: retain async fails by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/40

## New Contributors
* @wsimmonds made their first contribution in https://github.com/vectorize-io/hindsight/pull/39

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.1.7...v0.1.8

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.8)

---

## v0.1.7: v0.1.7
**Published:** 2025-12-16

## What's Changed
* ci: check compatibility with python 3.11, 3.12 and 3.13 by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/35


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.1.6...v0.1.7

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.7)

---

## v0.1.6: v0.1.6
**Published:** 2025-12-16

## What's Changed
* enable model tests on ci by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/29
* feat: add local mcp server by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/32
* feat: support for gemini-3-pro and gpt-5.2 by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/30
* bump pg0 0.11.x and improve documentation by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/33
* fix: doc build and lint files by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/34


**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.1.5...v0.1.6

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.6)

---

## v0.1.5: v0.1.5
**Published:** 2025-12-15

## What's Changed
* Fix base CI issues and the defaults in .env.example by @dcbouius in https://github.com/vectorize-io/hindsight/pull/24
* fix: upgrade Next.js to 16.0.10 to patch CVE-2025-55184 and CVE-2025-55183 by @dcbouius in https://github.com/vectorize-io/hindsight/pull/25
* feat: add optional graph retriever MPFP by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/26
* fix: add DOM.Iterable lib to resolve URLSearchParams type errors by @cdbartholomew in https://github.com/vectorize-io/hindsight/pull/27
* switch to pg0-embedded by @nicoloboschi in https://github.com/vectorize-io/hindsight/pull/28
* Fix contributing info by @dcbouius in https://github.com/vectorize-io/hindsight/pull/16
* Added hindsight_liteLLM implementation by @DK09876 in https://github.com/vectorize-io/hindsight/pull/17

## New Contributors
* @DK09876 made their first contribution in https://github.com/vectorize-io/hindsight/pull/17

**Full Changelog**: https://github.com/vectorize-io/hindsight/compare/v0.1.4...v0.1.5

[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.5)

---

## v0.1.4: v0.1.4
**Published:** 2025-12-11

## Quick Start

```bash
# Install the CLI
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash

# Start the server
docker run -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=openai \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  -e HINDSIGHT_API_LLM_MODEL=gpt-4o-mini \
  ghcr.io/vectorize-io/hindsight:0.1.4
```

## Docker Images
- `ghcr.io/vectorize-io/hindsight:0.1.4` - Standalone (recommended)
- `ghcr.io/vectorize-io/hindsight-api:0.1.4` - API only
- `ghcr.io/vectorize-io/hindsight-control-plane:0.1.4` - Web UI only

## CLI
```bash
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash
```

## Python
```bash
pip install hindsight-all  # or hindsight-api, hindsight-client
```

## TypeScript/JavaScript
```bash
npm install @vectorize-io/hindsight-client
```

## Helm
```bash
helm install hindsight oci://ghcr.io/vectorize-io/charts/hindsight --version 0.1.4
```


[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.4)

---

## v0.1.3: v0.1.3
**Published:** 2025-12-11

## Quick Start

```bash
# Install the CLI
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash

# Start the server
docker run -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=openai \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  -e HINDSIGHT_API_LLM_MODEL=gpt-4o-mini \
  ghcr.io/vectorize-io/hindsight:0.1.3
```

## Docker Images
- `ghcr.io/vectorize-io/hindsight:0.1.3` - Standalone (recommended)
- `ghcr.io/vectorize-io/hindsight-api:0.1.3` - API only
- `ghcr.io/vectorize-io/hindsight-control-plane:0.1.3` - Web UI only

## CLI
```bash
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash
```

## Python
```bash
pip install hindsight-all  # or hindsight-api, hindsight-client
```

## TypeScript/JavaScript
```bash
npm install @vectorize-io/hindsight-client
```

## Helm
```bash
helm install hindsight oci://ghcr.io/vectorize-io/charts/hindsight --version 0.1.3
```


[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.3)

---

## v0.1.2: v0.1.2
**Published:** 2025-12-10

## Quick Start

```bash
# Install the CLI
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash

# Start the server
docker run -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=openai \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  -e HINDSIGHT_API_LLM_MODEL=gpt-4o-mini \
  ghcr.io/vectorize-io/hindsight:0.1.2
```

## Docker Images
- `ghcr.io/vectorize-io/hindsight:0.1.2` - Standalone (recommended)
- `ghcr.io/vectorize-io/hindsight-api:0.1.2` - API only
- `ghcr.io/vectorize-io/hindsight-control-plane:0.1.2` - Web UI only

## CLI
```bash
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash
```

## Python
```bash
pip install hindsight-all  # or hindsight-api, hindsight-client
```

## TypeScript/JavaScript
```bash
npm install @vectorize-io/hindsight-client
```

## Helm
```bash
helm install hindsight oci://ghcr.io/vectorize-io/charts/hindsight --version 0.1.2
```


[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.2)

---

## v0.1.1: v0.1.1
**Published:** 2025-12-10

## Quick Start

```bash
# Install the CLI
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash

# Start the server
docker run -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=openai \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  -e HINDSIGHT_API_LLM_MODEL=gpt-4o-mini \
  ghcr.io/vectorize-io/hindsight:0.1.1
```

## Docker Images
- `ghcr.io/vectorize-io/hindsight:0.1.1` - Standalone (recommended)
- `ghcr.io/vectorize-io/hindsight-api:0.1.1` - API only
- `ghcr.io/vectorize-io/hindsight-control-plane:0.1.1` - Web UI only

## CLI
```bash
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash
```

## Python
```bash
pip install hindsight-all  # or hindsight-api, hindsight-client
```

## TypeScript/JavaScript
```bash
npm install @vectorize-io/hindsight-client
```

## Helm
```bash
helm install hindsight oci://ghcr.io/vectorize-io/charts/hindsight --version 0.1.1
```


[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.1)

---

## v0.1.0: v0.1.0
**Published:** 2025-12-09

## Quick Start

```bash
# Install the CLI
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash

# Start the server
docker run -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=openai \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  -e HINDSIGHT_API_LLM_MODEL=gpt-4o-mini \
  ghcr.io/vectorize-io/hindsight:0.1.0
```

## Docker Images
- `ghcr.io/vectorize-io/hindsight:0.1.0` - Standalone (recommended)
- `ghcr.io/vectorize-io/hindsight-api:0.1.0` - API only
- `ghcr.io/vectorize-io/hindsight-control-plane:0.1.0` - Web UI only

## CLI
```bash
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash
```

## Python
```bash
pip install hindsight-all  # or hindsight-api, hindsight-client
```

## TypeScript/JavaScript
```bash
npm install @vectorize-io/hindsight-client
```

## Helm
```bash
helm install hindsight oci://ghcr.io/vectorize-io/charts/hindsight --version 0.1.0
```


[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.1.0)

---

## v0.0.21: v0.0.21
**Published:** 2025-12-05

## Quick Start

```bash
# Install the CLI
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash

# Start the server
docker run -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=openai \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  -e HINDSIGHT_API_LLM_MODEL=gpt-4o-mini \
  ghcr.io/vectorize-io/hindsight:0.0.21
```

## Docker Images
- `ghcr.io/vectorize-io/hindsight:0.0.21` - Standalone (recommended)
- `ghcr.io/vectorize-io/hindsight-api:0.0.21` - API only
- `ghcr.io/vectorize-io/hindsight-control-plane:0.0.21` - Web UI only

## CLI
```bash
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash
```

## Python
```bash
pip install hindsight-all  # or hindsight-api, hindsight-client
```

## TypeScript/JavaScript
```bash
npm install @vectorize-io/hindsight-client
```

## Helm
```bash
helm install hindsight oci://ghcr.io/vectorize-io/charts/hindsight --version 0.0.21
```


[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.0.21)

---

## v0.0.18: v0.0.18
**Published:** 2025-12-04

## Quick Start

```bash
# Install the CLI
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash

# Start the server
docker run -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=openai \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  -e HINDSIGHT_API_LLM_MODEL=gpt-4o-mini \
  ghcr.io/vectorize-io/hindsight:0.0.18
```

## Docker Images
- `ghcr.io/vectorize-io/hindsight:0.0.18` - Standalone (recommended)
- `ghcr.io/vectorize-io/hindsight-api:0.0.18` - API only
- `ghcr.io/vectorize-io/hindsight-control-plane:0.0.18` - Web UI only

## CLI
```bash
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash
```

## Python
```bash
pip install hindsight-all  # or hindsight-api, hindsight-client
```

## TypeScript/JavaScript
```bash
npm install @vectorize-io/hindsight-client
```

## Helm
```bash
helm install hindsight oci://ghcr.io/vectorize-io/charts/hindsight --version 0.0.18
```


[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.0.18)

---

## v0.0.16: v0.0.16
**Published:** 2025-12-04

## Quick Start

```bash
# Install the CLI
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash

# Start the server
docker run -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=openai \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  -e HINDSIGHT_API_LLM_MODEL=gpt-4o-mini \
  ghcr.io/vectorize-io/hindsight:0.0.16
```

## Docker Images
- `ghcr.io/vectorize-io/hindsight:0.0.16` - Standalone (recommended)
- `ghcr.io/vectorize-io/hindsight-api:0.0.16` - API only
- `ghcr.io/vectorize-io/hindsight-control-plane:0.0.16` - Web UI only

## CLI
```bash
curl -fsSL https://raw.githubusercontent.com/vectorize-io/hindsight/refs/heads/main/hindsight-cli/install.sh | bash
```

## Python
```bash
pip install hindsight-all  # or hindsight-api, hindsight-client
```

## TypeScript/JavaScript
```bash
npm install @vectorize-io/hindsight-client
```

## Helm
```bash
helm install hindsight oci://ghcr.io/vectorize-io/charts/hindsight --version 0.0.16
```


[View on GitHub](https://github.com/vectorize-io/hindsight/releases/tag/v0.0.16)

---

