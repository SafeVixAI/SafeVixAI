# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import sys
from pathlib import Path

CHATBOT_DIR = Path(__file__).resolve().parent.parent
if str(CHATBOT_DIR) not in sys.path:
    sys.path.insert(0, str(CHATBOT_DIR))

import asyncio  # noqa: E402

from config import get_settings  # noqa: E402
from rag.vectorstore import LocalVectorStore  # noqa: E402


async def main() -> None:
    settings = get_settings()
    vectorstore = LocalVectorStore(
        database_url=settings.database_url,
        data_dir=settings.rag_data_dir
    )
    await vectorstore.build_index(force=True)


if __name__ == '__main__':
    asyncio.run(main())
