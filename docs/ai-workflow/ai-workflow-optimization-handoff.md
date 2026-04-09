# AI Workflow Optimization Handoff

## Purpose

This document is a handoff brief for another AI to optimize the three workflow documents in `docs/ai-workflow/`.

The goal is not to redesign the whole framework from scratch. The goal is to improve clarity, structure, and practical usefulness while preserving the core intent that emerged from the conversation.

## Documents To Optimize

Current documents:

- [personal-level-baseline.md](/Users/jerry_hu/AI/docs/ai-workflow/personal-level-baseline.md)
- [project-level-governance.md](/Users/jerry_hu/AI/docs/ai-workflow/project-level-governance.md)
- [lab-level-experiment-mode.md](/Users/jerry_hu/AI/docs/ai-workflow/lab-level-experiment-mode.md)

## High-Level Outcome We Reached

The final framework is a three-level AI workflow model:

- `personal-level`
  Defines how the assistant should think and collaborate with the user across all tasks.
- `project-level`
  Defines how AI should operate inside a real engineering repo with reusable assets, boundaries, and validation.
- `lab-level`
  Defines a lightweight research and experimentation mode for one-off exploration, evaluation, and trial work.

The key conclusion was:

- The user should not use one heavy process for every task.
- The user needs different operating modes for:
  - long-term personal collaboration
  - formal engineering repos
  - AI lab / research / exploration work

## Why This Work Started

The conversation started from analyzing external materials around Hermes Agent and a Glue Coding article, then moved into the user's own workflow.

The user wanted to understand:

- what Hermes Agent is
- whether it is fully open source
- whether it supports Feishu or WeChat
- whether it can run inside a LAN or internal network
- what Hermes self-evolution means in practice
- what "Glue Coding" actually means for the user's own projects

From there, the conversation shifted from external analysis to internal workflow design:

- What is the user's real stack?
- What are the user's coding habits?
- How should the user absorb the Glue Coding idea?
- Should the same heavy project workflow apply to all AI usage?

The answer became the three-level model above.

## Research Process Used In This Conversation

The analysis was not based on abstract opinions. It came from four different inputs:

### 1. Hermes Agent repo and docs analysis

We investigated:

- GitHub repo
- official docs
- install flow
- API server
- messaging platforms
- provider model
- MCP support
- deployment assumptions

Key URLs used:

- [Hermes Agent repo](https://github.com/NousResearch/hermes-agent)
- [Installation](https://hermes-agent.nousresearch.com/docs/getting-started/installation/)
- [AI Providers](https://hermes-agent.nousresearch.com/docs/integrations/providers/)
- [API Server](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server/)
- [MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp/)
- [Webhooks](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/webhooks)
- [Open WebUI integration](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/open-webui/)

### 2. Hermes self-evolution repo analysis

We investigated the companion repo and concluded it is an offline optimization pipeline, not a mature general self-evolving agent runtime.

Key URL used:

- [Hermes Agent Self-Evolution repo](https://github.com/NousResearch/hermes-agent-self-evolution)

### 3. Original WeChat article analysis via Playwright

The Glue Coding article was not analyzed only through mirrors or summaries. The original WeChat article was opened and read with browser automation.

Original article URL:

- [97.9%采纳率，胶水编程：业务需求出码最佳实践【天猫AI Coding实践系列】](https://mp.weixin.qq.com/s/G3aKbzdGUyD2h1aVjvbr2g)

The article was important because it introduced a strong engineering model:

- AI should mostly copy, adapt, and assemble
- not invent most code from scratch
- SPEC defines intent
- reusable materials define execution

### 4. Local repo scan of the user's actual codebase

We inspected the user's real repo collection here:

- `/Users/jerry_hu/Desktop/bes_tool/giteeCode`

This was necessary because the user explicitly challenged the assistant to stop speaking in generic terms and instead infer the user's real stack and habits from actual repositories.

## What We Learned About The User

The user's real engineering profile is not generic SaaS/web app work.

The user's stack and project evidence show:

- main languages: `Python` and `C/C++`
- main desktop/app framework: `PySide6` and `Qt6`
- domain focus: chip-related tools, embedded-related tooling, communication tools
- repeated technical themes:
  - serial communication
  - HID / OTA tools
  - binary / struct parsing
  - firmware-adjacent workflows
  - device diagnostics
  - build and packaging
  - cross-platform behavior

Representative local repos inspected:

- `/Users/jerry_hu/Desktop/bes_tool/giteeCode/chip-deug-tool`
- `/Users/jerry_hu/Desktop/bes_tool/giteeCode/nv-ram-edit-tool`
- `/Users/jerry_hu/Desktop/bes_tool/giteeCode/bes-ui-tool`
- `/Users/jerry_hu/Desktop/bes_tool/giteeCode/serial-comm-api-demo`
- `/Users/jerry_hu/Desktop/bes_tool/giteeCode/usb_hid_ota_tools_windows`
- `/Users/jerry_hu/Desktop/bes_tool/giteeCode/usb_hid_ota_tools_macos`
- `/Users/jerry_hu/Desktop/bes_tool/giteeCode/besotaupdate`
- `/Users/jerry_hu/Desktop/bes_tool/giteeCode/transfer_dylib`

Representative file evidence:

- [chip-deug-tool/pyproject.toml](/Users/jerry_hu/Desktop/bes_tool/giteeCode/chip-deug-tool/pyproject.toml)
- [nv-ram-edit-tool/pyproject.toml](/Users/jerry_hu/Desktop/bes_tool/giteeCode/nv-ram-edit-tool/pyproject.toml)
- [bes-ui-tool/BesToolDemo/requirements.txt](/Users/jerry_hu/Desktop/bes_tool/giteeCode/bes-ui-tool/BesToolDemo/requirements.txt)
- [serial-comm-api-demo/requirements.txt](/Users/jerry_hu/Desktop/bes_tool/giteeCode/serial-comm-api-demo/requirements.txt)
- [Chip_Debug_Tool.py](/Users/jerry_hu/Desktop/bes_tool/giteeCode/chip-deug-tool/Chip_Debug_Tool.py)
- [serial-comm-api-demo/modules/logger_manager.py](/Users/jerry_hu/Desktop/bes_tool/giteeCode/serial-comm-api-demo/modules/logger_manager.py)
- [serial-comm-api-demo/modules/multi_serial_manager.py](/Users/jerry_hu/Desktop/bes_tool/giteeCode/serial-comm-api-demo/modules/multi_serial_manager.py)
- [chip-deug-tool/build.py](/Users/jerry_hu/Desktop/bes_tool/giteeCode/chip-deug-tool/build.py)
- [nv-ram-edit-tool/build.py](/Users/jerry_hu/Desktop/bes_tool/giteeCode/nv-ram-edit-tool/build.py)

## What We Learned About The User's Preferred AI Collaboration Style

The user provided a strong prompt describing how the assistant should work with them.

The prompt established these stable preferences:

- act like a senior engineering mentor
- prioritize reasoning before code
- focus on hardware constraints, memory, and interop tradeoffs
- prefer step-by-step guidance over full implementation
- explain debugging in real systems, especially hardware/software boundaries
- avoid silent fixes
- train engineering skill, not just generate code

Important collaboration constraint:

- do not directly write or modify final code unless the user explicitly says:
  - `write the final code`
  - `apply this change`

This preference matches the user's actual repo and domain.

## What We Concluded About Glue Coding

The user proposed a practical interpretation:

- reusable modules should be treated as long-term assets
- examples include:
  - UI modules
  - logging modules
  - packaging modules
  - serial communication modules
- AI should mainly write the final 10% of glue
- SPEC should define framework, constraints, style, structure, boundaries, and verification

We agreed with this, but refined it:

- for the user's domain, "knowledge base" is not enough
- the user actually needs reusable engineering assets
- especially:
  - protocol / communication assets
  - UI skeleton assets
  - logging / diagnostics assets
  - packaging / distribution assets
  - binary / parsing assets

This is the reason the project-level document focuses on:

- `AGENTS.md`
- `spec-template.md`
- `module-catalog.md`
- `templates/`
- `playbooks/`

## Key External Findings That Influenced The Design

### Hermes Agent findings

- Hermes Agent is a strong open repo for a self-hosted agent runtime, but it is not a pure local all-in-one closed-loop system.
- It relies on configured model providers, though it also supports self-hosted endpoints.
- It has useful concepts for:
  - skills
  - MCP
  - messaging gateways
  - API server
  - hooks and webhooks

Relevant links:

- [Hermes Agent repo](https://github.com/NousResearch/hermes-agent)
- [API Server](https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server/)
- [MCP](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp/)
- [Webhooks](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/webhooks)
- [AI Providers](https://hermes-agent.nousresearch.com/docs/integrations/providers/)

### Feishu / WeChat support conclusion

- Hermes Agent does not have first-party built-in Feishu or WeChat support.
- Feishu could likely be bridged via Hermes API server or webhooks.
- Personal WeChat is not a clean target.
- Enterprise WeChat or public-account style integration could be bridged externally, but not out of the box.

### Internal network / LAN conclusion

- Hermes can run in a LAN or internal network.
- Fully air-gapped deployment is possible in principle but not the default happy path.
- Local/self-hosted model endpoints make LAN deployment realistic.

### Hermes self-evolution conclusion

- The self-evolution repo is useful as an offline optimization concept.
- It is not a mature general-purpose self-improving agent platform.
- The strongest reusable idea is offline evaluation + optimization + guardrails.

### Glue Coding article conclusions

The strongest ideas extracted from the article were:

- AI should mostly copy/adapt/assemble, not invent most code
- SPEC handles intent
- reusable materials handle execution
- the article describes a four-layer system:
  - task spec
  - development rules
  - code patterns
  - domain knowledge
- static and dynamic context injection should be separated
- `AGENTS.md` is a real engineering control point, not decorative metadata

## The Core User Need

The user did not just want a summary of articles and repos.

The real need was:

- build a usable AI workflow model that fits the user's real engineering life
- avoid generic internet-style AI coding advice
- create something that works for both:
  - serious engineering repos
  - lighter research and AI lab work

The user explicitly pushed against over-generalized answers and wanted repo-grounded analysis.

## Why The Three-Level Split Was Necessary

This was the central design decision.

Without the split, one of two bad outcomes happens:

- either the workflow is too heavy for daily use and research
- or it is too vague to govern real engineering repos

The three levels solve that:

### Personal level

This is the user's cross-cutting thinking and collaboration baseline.

It should cover:

- first-principles analysis
- no guessing unclear intent
- root cause before patch
- concise output
- different depth for low-risk vs high-risk problems
- mentor-style reasoning before code

### Project level

This is for formal repos and repeatable engineering work.

It should cover:

- asset reuse
- repo-specific rules
- allowed change boundaries
- validation methods
- templates
- module catalog
- debugging playbooks

### Lab level

This is for AI lab / exploration / research mode.

It should stay light and focus on:

- minimal validation
- experiment question
- hypothesis
- findings
- whether to discard, keep as note, or promote to project-level assets

## Important Boundary Conditions For The Next AI

When optimizing the three docs, do not collapse them into one generic workflow.

Preserve these boundaries:

- `personal-level` is always on and should remain lightweight
- `project-level` is repo-scoped and should remain heavier
- `lab-level` should remain light and anti-bureaucratic

Do not optimize them by making all three look structurally identical.

That would defeat the point of the split.

## What The Next AI Should Improve

The optimization target is:

- sharper wording
- clearer triggers for when to use each level
- less overlap between levels
- more actionable field definitions
- better reuse of the user's actual domain language

The optimization target is not:

- inventing a new framework
- flattening all three levels into one universal template
- turning the lab-level doc into project governance
- turning the personal-level doc into a full project manual

## Suggested Optimization Questions

The next AI should ask itself:

1. Does each document have a clear, non-overlapping job?
2. Is the user's embedded / chip-tooling / Qt / comms domain visible enough?
3. Is the boundary between research work and engineering work explicit enough?
4. Are the documents practical enough that the user could really use them?
5. Are the documents concise enough to remain usable?

## Current Best Interpretation Of The User's Intent

The user wants an AI operating model that:

- respects the user's engineering maturity goals
- improves decision quality, not just code output speed
- supports real hardware-adjacent software work
- preserves reusable engineering assets
- lets light experimentation stay light
- avoids forcing one rigid workflow on every task

## If The Next AI Needs A One-Paragraph Summary

The user is a Python + C/C++ engineer working on chip-related and embedded-related desktop tooling, mainly with PySide6/Qt6, device communication, parsing, diagnostics, and packaging. We analyzed Hermes Agent, Hermes self-evolution, the original Glue Coding article, and the user's own repos. The result was a three-level AI workflow model: personal-level for thinking/collaboration defaults, project-level for formal repo governance and asset reuse, and lab-level for lightweight AI experiments and research. The next AI should optimize those three docs without flattening them into one generic workflow.
