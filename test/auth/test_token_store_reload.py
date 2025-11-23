#!/usr/bin/env python3
"""Test that AuthService can see tokens created after initialization

This test verifies that when a token is created by one process and written
to the shared token store, another AuthService instance can verify it.

This simulates the real scenario where:
1. MCP/Web servers start with AuthService
2. Tests create tokens via separate AuthService instance
3. Servers must be able to verify those newly-created tokens
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import tempfile
import time
from app.auth import AuthService
from app.logger import ConsoleLogger
import logging


def test_auth_service_sees_externally_created_tokens():
    """Test that AuthService can verify tokens created after initialization"""
    logger = ConsoleLogger(name="token_reload_test", level=logging.INFO)

    # Use a temporary token store for this test
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        token_store_path = f.name
        f.write("{}")  # Initialize empty store

    try:
        # Step 1: Start "server" AuthService (simulates server startup)
        logger.info("Step 1: Initializing server AuthService")
        server_auth = AuthService(
            secret_key="test-secret-for-reload-test", token_store_path=token_store_path
        )
        logger.info("Server AuthService initialized", token_count=len(server_auth.token_store))

        # Verify server starts with empty token store
        assert len(server_auth.token_store) == 0, "Server should start with no tokens"

        # Step 2: Create token using separate "test" AuthService (simulates test creating token)
        logger.info("Step 2: Creating token via separate test AuthService")
        test_auth = AuthService(
            secret_key="test-secret-for-reload-test", token_store_path=token_store_path
        )
        token = test_auth.create_token(group="test_group", expires_in_seconds=3600)
        logger.info("Token created", token_length=len(token))

        # Verify test service has the token
        assert len(test_auth.token_store) == 1, "Test service should have 1 token"

        # Small delay to ensure file system write is complete
        time.sleep(0.1)

        # Step 3: Verify server AuthService can see the new token
        logger.info("Step 3: Verifying server can see externally-created token")
        try:
            token_info = server_auth.verify_token(token)
            logger.info("SUCCESS: Server verified token", group=token_info.group)
            assert (
                token_info.group == "test_group"
            ), f"Expected group 'test_group', got {token_info.group}"
        except ValueError as e:
            logger.error("FAILURE: Server could not verify token", error=str(e))
            logger.error("Server token store", count=len(server_auth.token_store))
            logger.error("Test token store", count=len(test_auth.token_store))
            pytest.fail(f"Server AuthService could not verify externally-created token: {e}")

    finally:
        # Cleanup
        Path(token_store_path).unlink(missing_ok=True)


def test_auth_service_reloads_token_store_on_verify():
    """Test that verify_token always reloads from disk"""
    logger = ConsoleLogger(name="reload_verification_test", level=logging.INFO)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        token_store_path = f.name
        f.write("{}")

    try:
        # Create first service and token
        auth1 = AuthService(secret_key="test-secret-reload", token_store_path=token_store_path)
        auth1.create_token(group="group1", expires_in_seconds=3600)
        logger.info("First token created")

        # Create second service (simulates server that started before token was created)
        auth2 = AuthService(secret_key="test-secret-reload", token_store_path=token_store_path)

        # auth2's initial token_store should see token1 because it loads on init
        assert len(auth2.token_store) == 1, "Second service should see first token on init"

        # Create another token via auth1
        token2 = auth1.create_token(group="group2", expires_in_seconds=3600)
        logger.info("Second token created")

        time.sleep(0.1)

        # Now verify token2 via auth2 - this should trigger reload
        try:
            token_info = auth2.verify_token(token2)
            logger.info("SUCCESS: Second service verified second token", group=token_info.group)
            assert token_info.group == "group2"
        except ValueError as e:
            pytest.fail(f"Second service could not verify second token: {e}")

    finally:
        Path(token_store_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
