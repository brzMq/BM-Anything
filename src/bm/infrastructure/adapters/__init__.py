"""BM adapters package.

Adapters are the ONLY place that may reference third-party framework types
(LFX, execution engines, plugin hosts). They translate between an external
framework's objects and the framework-neutral ``bm.*`` contracts.
"""

from __future__ import annotations
