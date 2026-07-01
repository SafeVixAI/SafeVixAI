# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import sys
from pathlib import Path

CHATBOT_DIR = Path(__file__).resolve().parent.parent
if str(CHATBOT_DIR) not in sys.path:
    sys.path.insert(0, str(CHATBOT_DIR))

from config import get_settings
from rag.vectorstore import LocalVectorStore


import asyncio

async def main() -> None:
    settings = get_settings()
    vectorstore = LocalVectorStore(
        database_url=settings.database_url,
        data_dir=settings.rag_data_dir
    )
    await vectorstore.build_index(force=True)
    print(await vectorstore.stats())


if __name__ == '__main__':
    asyncio.run(main())
