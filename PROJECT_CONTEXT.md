# PROJECT_CONTEXT.md

# LLM Security Audit Gateway - Project Context

## 1. Project Purpose

This project is a FastAPI-based **LLM Security Audit Gateway**.

The goal is to build a lightweight gateway between users and an external LLM API. Instead of allowing users to call the LLM provider directly, all requests should pass through this gateway first.

The gateway is designed to provide:

* API key authentication
* Prompt risk scanning
* Security alert logging
* Rate limiting
* Chat logging
* Token usage tracking
* Basic auditability for LLM requests

This project is intended to become a portfolio project for internship applications, especially for roles related to:

* Data Science Intern
* Cybersecurity Intern
* Security Analyst Intern
* Backend Intern
* AI / LLM Security Intern

---

## 2. Current Project Management Method

This project is managed using three main layers:

1. **GitHub Repository**
2. **ChatGPT Project Sources**
3. **PROJECT_STATUS.md**

The GitHub repository is used for actual source code and version control.

ChatGPT Project Sources are used as the shared knowledge base for AI-assisted planning, code review, debugging, and progress tracking.

`PROJECT_STATUS.md` is the source of truth for project progress.

When there is a conflict between chat history, memory, and uploaded project files, the priority order should be:

```text
1. Latest uploaded source files
2. PROJECT_STATUS.md
3. Current chat context
4. Older chat history
```

The assistant should not assume a feature is completed unless it is either:

* Listed in `PROJECT_STATUS.md`
* Clearly visible in the uploaded source files

---

## 3. Role of ChatGPT Project

The ChatGPT Project is used as a central workspace for this project.

It helps with:

* Code review
* Debugging
* Feature planning
* Explaining concepts
* Writing README and documentation
* Preparing commit messages
* Planning future project milestones
* Keeping different chats aligned through shared Sources

Different chats inside the same Project may be used for different purposes, for example:

* One chat for debugging
* One chat for feature planning
* One chat for code review
* One chat for documentation
* One chat for internship portfolio preparation

However, chats do not automatically share full conversation history perfectly. Therefore, shared files in Project Sources are important for keeping progress aligned.

---

## 4. Role of Project Sources

Project Sources are the shared reference files uploaded into the ChatGPT Project.

Sources should include stable project files such as:

```text
main.py
auth.py
crud.py
database.py
init_db.py
prompt_scanner.py
security_alerts.py
rate_limiter.py
README.md
requirements.txt
.env.example
PROJECT_STATUS.md
PROJECT_CONTEXT.md
```

Project Sources should not include sensitive or local-only files such as:

```text
.env
.venv/
__pycache__/
*.pyc
*.db
secure_gateway.db
```

The purpose of Sources is to make sure future chats can understand the actual current state of the project.

When asking for code review, debugging, or planning, the assistant should first inspect the relevant uploaded source files instead of guessing from old chat history.

---

## 5. Role of Chats

Chats are used for discussion and task execution.

A chat may contain:

* Explanations
* Debugging steps
* Temporary test results
* Code suggestions
* Learning notes
* Planning discussion

However, chat messages are not the best place to store long-term project truth.

Important decisions, completed features, and next steps should be moved into `PROJECT_STATUS.md`.

Reusable project background should be moved into `PROJECT_CONTEXT.md`.

---

## 6. Role of PROJECT_STATUS.md

`PROJECT_STATUS.md` is the source of truth for project progress.

It should record:

* Current project version
* Project goal
* Completed features
* Recent fixes
* Known issues
* Next tasks
* Important decisions

Before giving feature planning, next-step suggestions, or final code review conclusions, the assistant should check `PROJECT_STATUS.md` first if it is available.

A feature should not be treated as completed unless it is recorded in `PROJECT_STATUS.md` or visible in the latest uploaded source files.

Recommended structure:

```md
# LLM Security Audit Gateway - Project Status

## Current Version

## Project Goal

## Completed Features

## Recent Fixes

## Known Issues

## Next Tasks

## Important Decisions
```

---

## 7. Role of PROJECT_CONTEXT.md

`PROJECT_CONTEXT.md` stores long-term project management context.

It explains how the project is organized, how ChatGPT Project should be used, how Sources work, and how different chats should stay synchronized.

This file is not mainly about technical implementation details.

It is mainly about:

* Project workflow
* Source management
* Chat synchronization
* Progress tracking
* AI collaboration rules

This file should be updated only when the project management method changes.

---

## 8. How to Sync Progress Across Different Chats

Because different chats may not perfectly know what happened in other chats, progress should be synchronized through files.

After finishing a debugging task, feature implementation, or code review, do the following:

### Step 1: Update the source code locally

Make sure the actual project files are modified and tested.

### Step 2: Test the feature

Use Swagger UI, terminal commands, or scripts to verify that the feature works.

Example checks:

```text
API key authentication works
Prompt scanner blocks high-risk prompts
Security alerts are written to database
Rate limiter returns 429 after exceeding limit
Normal chat requests are logged
```

### Step 3: Commit to GitHub

Use concise conventional-style commit messages.

Examples:

```text
feat: add user-based rate limiting
refactor: use async httpx for LLM API calls
fix: hide provider authentication error details
docs: update project context
```

### Step 4: Update PROJECT_STATUS.md

Add the completed feature, recent fix, known issue, or next task.

### Step 5: Upload latest files to Project Sources

Upload the latest important files into ChatGPT Project Sources, especially:

```text
PROJECT_STATUS.md
main.py
auth.py
rate_limiter.py
prompt_scanner.py
security_alerts.py
README.md
requirements.txt
.env.example
```

### Step 6: Start future chats by asking the assistant to read PROJECT_STATUS.md

Recommended prompt:

```text
请先读取 PROJECT_STATUS.md，只基于当前项目状态规划下一步，不要假设未记录的进度。
```

---

## 9. Progress Sync Summary Rule

When a debugging or code review task is finished, the assistant should provide a short progress sync summary that can be copied into `PROJECT_STATUS.md`.

Recommended format:

```md
## Recent Fixes
- YYYY-MM-DD: Short description of the completed fix or feature.

## Known Issues
- Short description of remaining issue.

## Next Tasks
1. Next concrete task
2. Next concrete task
```

This helps prevent progress mismatch between different chats.

---

## 10. Role of Codex

Codex can be used as an AI coding assistant or coding agent.

It may help with:

* Editing files
* Refactoring code
* Generating tests
* Fixing bugs
* Implementing planned features

However, Codex should not replace project status tracking.

If Codex modifies the project, the changes should still be:

1. Reviewed manually
2. Tested locally
3. Committed to GitHub
4. Recorded in `PROJECT_STATUS.md`
5. Reflected in uploaded Project Sources

Codex output should not be treated as completed progress until the code is visible in the repository or uploaded source files.

---

## 11. Secret Management Rules

Never upload real secrets to GitHub or ChatGPT Project Sources.

Do not upload:

```text
.env
real API keys
database files containing private logs
credentials
tokens
```

Use `.env.example` instead.

Example `.env.example`:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-v4-flash

RATE_LIMIT_MAX_REQUESTS=5
RATE_LIMIT_WINDOW_SECONDS=60
```

The real `.env` file should stay local only.

If a real API key is accidentally exposed in a screenshot, chat, or repository, it should be deleted or rotated immediately.

---

## 12. Current Project Direction

The project is currently moving from a basic LLM API wrapper toward a security-focused LLM gateway.

The main completed direction includes:

* Authentication
* Prompt scanning
* Security alert logging
* Rate limiting
* Environment variable handling
* Basic README documentation

The next project direction should focus on improving engineering quality and auditability.

Recommended future work:

```text
1. Add pytest tests for authentication and rate limiting
2. Confirm database logging works correctly
3. Improve error response format
4. Add structured security alert logs
5. Improve README setup instructions
6. Prepare GitHub portfolio description
7. Add analytics or dashboard later
```

---

## 13. Assistant Behavior Rules for This Project

When helping with this project, the assistant should:

* Explain in Chinese first, with English technical terms when useful
* Check `PROJECT_STATUS.md` before planning next steps
* Review code by identifying issue, risk, fix, and urgency
* Avoid unsafe advice such as exposing real API keys or committing secrets
* Use concise conventional-style commit messages
* Trust latest uploaded source files and `PROJECT_STATUS.md` over older chat history
* Not assume a feature is complete unless it appears in source files or `PROJECT_STATUS.md`

---

## 14. Recommended Startup Prompt for Future Chats

Use this prompt when starting a new chat inside this Project:

```text
请先读取 PROJECT_STATUS.md 和 PROJECT_CONTEXT.md。
只基于 Project Sources 中的最新文件判断项目状态。
不要假设未记录的进度。
请先总结目前已完成的功能、已知问题和下一步最合理任务。
```

This helps future chats stay aligned with the real project state.
