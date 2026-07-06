"""Benchmarks: throughput (requests per second) under concurrency."""

import time
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed


def _worker(client, route: str) -> int:
    resp = client.get(route)
    return resp.status_code


class TestThroughput:
    def _throughput(self, client, route: str, concurrency: int, n: int):
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(_worker, client, route) for _ in range(n)]
            results = [f.result() for f in as_completed(futures)]
        elapsed = time.perf_counter() - start
        rps = n / elapsed
        ok = sum(1 for s in results if s == 200)
        print(f"\n  {route}  |  {concurrency} workers  |  {n} req  |  {rps:.0f} RPS  |  {elapsed:.2f}s  |  {ok}/{n} ok")
        return rps

    def test_throughput_home_1w(self, client):
        rps = self._throughput(client, "/", concurrency=1, n=20)
        assert rps > 0

    def test_throughput_home_5w(self, client):
        rps = self._throughput(client, "/", concurrency=5, n=20)
        assert rps > 0

    def test_throughput_home_10w(self, client):
        rps = self._throughput(client, "/", concurrency=10, n=40)
        assert rps > 0

    def test_throughput_login_5w(self, client):
        rps = self._throughput(client, "/auth/login", concurrency=5, n=20)
        assert rps > 0

    def test_throughput_inicio_5w(self, client):
        rps = self._throughput(client, "/section/inicio", concurrency=5, n=20)
        assert rps > 0

    def test_throughput_servicios_5w(self, client):
        rps = self._throughput(client, "/section/servicios", concurrency=5, n=20)
        assert rps > 0
