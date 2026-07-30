# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
#!/usr/bin/env python3
"""Secrets rotation automation for SafeVixAI.

Rotates API keys, JWT secrets, and database passwords across all services.
Supports: AWS Secrets Manager, .env files (local dev), and K8s secrets.

Usage:
    python scripts/rotate-secrets.py --service backend --key JWT_SECRET_KEY
    python scripts/rotate-secrets.py --all --dry-run
    python scripts/rotate-secrets.py --ci  # CI mode: rotate + update K8s
"""

import argparse
import json
import os
import secrets
import string
import subprocess
import sys
import tempfile
from datetime import UTC, datetime

SECRETS_MANIFEST = {
    "backend": {
        "JWT_SECRET_KEY": {"length": 64, "type": "alphanumeric"},
        "ADMIN_SECRET": {"length": 32, "type": "complex"},
        "DATABASE_URL": {"type": "managed", "note": "Rotated via AWS RDS + Secrets Manager"},
    },
    "chatbot": {
        "GROQ_API_KEY": {"type": "managed", "note": "Rotate via Groq dashboard"},
        "GEMINI_API_KEY": {"type": "managed", "note": "Rotate via Google AI Studio"},
        "CEREBRAS_API_KEY": {"type": "managed", "note": "Rotate via Cerebras dashboard"},
        "HF_TOKEN": {"type": "managed", "note": "Rotate via HuggingFace settings"},
    },
    "infra": {
        "POSTGRES_PASSWORD": {"length": 24, "type": "complex"},
        "REDIS_PASSWORD": {"length": 24, "type": "complex"},
    },
}

AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")


def generate_secret(length: int, secret_type: str) -> str:
    if secret_type == "alphanumeric":
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))
    if secret_type == "complex":
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        return "".join(secrets.choice(alphabet) for _ in range(length))
    return secrets.token_urlsafe(length)


def rotate_local_env(service: str, key: str, new_value: str) -> bool:
    if service == "infra":
        env_path = ".env"
    elif service == "backend":
        env_path = "backend/.env"
    elif service == "chatbot":
        env_path = "chatbot_service/.env"
    else:
        return False

    if not os.path.exists(env_path):
        print(f"  ⚠ {env_path} not found, skipping")
        return False

    with open(env_path) as f:
        lines = f.readlines()

    found = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}=") or line.startswith(f"export {key}="):
            prefix = "export " if line.startswith("export ") else ""
            new_lines.append(f"{prefix}{key}={new_value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"{key}={new_value}\n")

    # .env files intentionally store secrets in plaintext for local dev — this is by design
    with open(env_path, "w") as f:
        f.writelines(new_lines)

    return True


def rotate_aws_secret(secret_name: str, new_value: str) -> bool:
    # Write secret to temp file to avoid exposing it in process args
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    try:
        tmp.write(new_value)
        tmp.close()
        result = subprocess.run(
            ["aws", "secretsmanager", "put-secret-value",
             "--secret-id", secret_name,
             "--secret-string", f"file://{tmp.name}",
             "--region", AWS_REGION],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return True
        print(f"  ⚠ AWS error: {result.stderr.strip()}")
        return False
    except FileNotFoundError:
        print("  ⚠ AWS CLI not installed")
        return False
    except subprocess.TimeoutExpired:
        print("  ⚠ AWS CLI timed out")
        return False
    finally:
        os.unlink(tmp.name)


def rotate_k8s_secret(secret_name: str, key: str, new_value: str) -> bool:
    # Build secret manifest and pipe through stdin to avoid secret in process args
    secret_manifest = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": secret_name, "namespace": "safevixai"},
        "type": "Opaque",
        "stringData": {key: new_value},
    }
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    try:
        json.dump(secret_manifest, tmp)
        tmp.close()
        result = subprocess.run(
            ["kubectl", "apply", "-f", tmp.name],
            capture_output=True, text=True, timeout=15,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    finally:
        os.unlink(tmp.name)


def main():
    parser = argparse.ArgumentParser(description="SafeVixAI secrets rotation")
    parser.add_argument("--service", choices=["backend", "chatbot", "infra"],
                        help="Service to rotate secrets for")
    parser.add_argument("--key", help="Specific key to rotate")
    parser.add_argument("--all", action="store_true", help="Rotate all auto-generated secrets")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without doing it")
    parser.add_argument("--ci", action="store_true", help="CI mode: rotate + push to AWS + K8s")
    args = parser.parse_args()

    services = [args.service] if args.service else list(SECRETS_MANIFEST.keys())

    rotation_log = {
        "timestamp": datetime.now(UTC).isoformat(),
        "rotations": [],
    }

    for service in services:
        secrets_config = SECRETS_MANIFEST[service]
        keys = [args.key] if args.key else list(secrets_config.keys())

        for key in keys:
            config = secrets_config[key]

            if config.get("type") == "managed":
                print(f"  ↪ {service}/{key}: managed externally ({config.get('note', '')})")
                continue

            new_value = generate_secret(config["length"], config["type"])

            print(f"  ↪ Rotating {service}/{key} ...")

            if args.dry_run:
                print(f"     DRY-RUN: would rotate {service}/{key}")
                rotation_log["rotations"].append({
                    "service": service, "key": key, "dry_run": True,
                })
                continue

            rotated_local = rotate_local_env(service, key, new_value)
            exit_code = 0

            if args.ci:
                aws_secret_name = f"safevixai-{service}-env"
                rotated_aws = rotate_aws_secret(aws_secret_name, json.dumps({key: new_value}))
                if not rotated_aws:
                    exit_code = 1

                k8s_secret_name = f"safevixai-{service}-secrets"
                rotated_k8s = rotate_k8s_secret(k8s_secret_name, key, new_value)
                if not rotated_k8s:
                    exit_code = 1

            rotation_log["rotations"].append({
                "service": service, "key": key, "rotated_local": rotated_local,
            })

    rotation_log_path = f"rotation-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(rotation_log_path, "w") as f:
        json.dump(rotation_log, f, indent=2)
    print(f"\n✓ Rotation log written to {rotation_log_path}")
    print(f"✓ {len(rotation_log['rotations'])} key(s) processed")

    sys.exit(0)


if __name__ == "__main__":
    main()
