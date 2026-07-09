# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
import glob
for f in glob.glob('tests/*.py'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if "def search(self, message):" in content:
        content = content.replace(
            "def search(self, message):",
            "async def search(self, message):"
        )
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
            
    if "def search(self, message: str) -> list:" in content:
        content = content.replace(
            "def search(self, message: str) -> list:",
            "async def search(self, message: str) -> list:"
        )
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
