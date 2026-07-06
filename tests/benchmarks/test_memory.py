"""Benchmarks: memory usage (RSS) before/after requests."""

import psutil
import os
import pytest


def _rss_mb() -> float:
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)


class TestMemory:
    def test_memory_baseline(self):
        mb = _rss_mb()
        print(f"\n  RSS baseline: {mb:.1f} MB")
        assert mb > 0

    def test_memory_after_10_requests(self, client):
        for _ in range(10):
            client.get("/")
        mb = _rss_mb()
        print(f"\n  RSS after 10× GET /: {mb:.1f} MB")
        assert mb > 0

    def test_memory_after_50_requests(self, client):
        for _ in range(50):
            client.get("/")
        mb = _rss_mb()
        print(f"\n  RSS after 50× GET /: {mb:.1f} MB")
        assert mb > 0

    def test_memory_after_mixed_routes(self, client):
        routes = ["/", "/auth/login", "/section/inicio", "/section/servicios", "/section/contacto"]
        for _ in range(10):
            for route in routes:
                client.get(route)
        mb = _rss_mb()
        print(f"\n  RSS after 50× mixed routes: {mb:.1f} MB")
        assert mb > 0

    def test_memory_growth_per_request(self, client):
        """Estima el crecimiento de memoria por request."""
        before = _rss_mb()
        n = 100
        for _ in range(n):
            client.get("/")
        after = _rss_mb()
        growth = (after - before) / n
        print(f"\n  RSS growth per request: {growth*1000:.2f} KB/req  (total Δ {after-before:.1f} MB en {n} req)")
        assert growth >= 0
