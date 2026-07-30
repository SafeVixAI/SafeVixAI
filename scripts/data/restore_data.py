# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""Run on new machine to restore large data files from HuggingFace."""
import os

from huggingface_hub import snapshot_download

snapshot_download(
    repo_id='YOUR_HF_USERNAME/safevixai-datasets',
    repo_type='dataset',
    local_dir='chatbot_service/data/',
    token=os.getenv('HF_TOKEN'),
)
print('Data restoration complete.')
