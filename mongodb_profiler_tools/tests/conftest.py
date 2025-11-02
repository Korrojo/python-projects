"""Shared test fixtures for mongodb_profiler_tools."""

import pytest


@pytest.fixture
def sample_slow_ops():
    """Sample slow operations for testing."""
    return [
        {
            "timestamp": "2024-01-15T10:30:00.000Z",
            "operation": "query",
            "namespace": "testdb.users",
            "millis": 250,
            "client": "192.168.1.100",
            "user": "testuser",
            "plan_summary": "COLLSCAN",
            "docs_examined": 1000,
            "keys_examined": 0,
            "n_returned": 10,
            "command": '{"find": "users", "filter": {"age": {"$gt": 25}}}',
        },
        {
            "timestamp": "2024-01-15T10:31:00.000Z",
            "operation": "update",
            "namespace": "testdb.orders",
            "millis": 150,
            "client": "192.168.1.101",
            "user": "adminuser",
            "plan_summary": "IXSCAN",
            "docs_examined": 100,
            "keys_examined": 100,
            "n_returned": 50,
            "command": '{"update": "orders", "updates": [{"q": {"status": "pending"}, "u": {"$set": {"status": "processed"}}}]}',
        },
    ]
