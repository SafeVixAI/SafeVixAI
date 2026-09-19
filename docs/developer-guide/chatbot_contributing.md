# Contributing to the Chatbot Team

To maintain high architectural standards and prevent merge conflicts in the `chatbot_service`, use this guide for development.

## Team Assignments
Assign ownership of specific modules before writing code.
- **Member A**: Providers (13 provider files), Memory, API endpoints.
- **Member B**: RAG, Agent (ChatEngine — 8 agent modules), Tools.
- **Member C**: Frontend Voice UI, Voice Output, and Multi-language setup.

## Workflow Rules
1. **GitHub Flow**: Always work on a feature branch (`chatbot/feature-name`).
2. **Commit Often**: Use small, focused commits.
3. **No Direct Push**: Push to GitHub and create a Pull Request (PR) for review.
4. **Peer Review**: Never merge your own PR. Let a team lead review first.

## Code Standards
- **Python**: Use Python 3.11 with `async/await`.
- **Typing**: Use TypeHints for function signatures.
- **Environment**: Keep all keys in `.env` and never commit it to Git.
- **Testing**: Add a corresponding test in the `/tests` folder for every new feature.

## Test State
- **892/892 tests passing**, **95% coverage**
- **pytest config**: `asyncio_mode = strict` — async tests **require** `@pytest.mark.asyncio` decorator
- Run: `pytest tests/ -q` from `chatbot_service/`
