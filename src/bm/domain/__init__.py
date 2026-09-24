"""BM-Anything Domain layer.

HARD CONSTRAINTS (enforced by tests/architecture/test_domain_no_oss_imports.py):

Modules under ``bm.domain.*`` MUST NOT import any of the following OSS
infrastructure SDKs:

    lfx, langflow, hatchet, temporalio, dbos,
    qdrant_client, psycopg, boto3, redis, opensearchpy

These belong in ``bm.infrastructure.*`` / ``bm.adapters.*`` / ``bm.providers.*``.
Domain code expresses business semantics only; adapters translate to SDK calls.

P0 ships an empty shell. Domain models (Capability, Artifact, Knowledge,
Workflow, Application, Evaluation) land in P2+.
"""

from __future__ import annotations

# Intentionally empty in P0.
