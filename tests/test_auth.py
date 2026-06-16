import pytest
from pathlib import Path
import gitflow.dashboard.api.auth as auth

def test_auth_token_flow(tmp_path, monkeypatch):
    temp_token_file = tmp_path / ".api_token"
    monkeypatch.setattr(auth, "TOKEN_FILE", temp_token_file)

    # Revoke initially to ensure clean state
    auth.revoke_token()

    # Generate token
    token = auth.generate_token()
    assert len(token) == 64
    assert temp_token_file.exists()
    assert temp_token_file.read_text().strip() == token

    # Get token
    assert auth.get_token() == token

    # Verify token
    assert auth.verify_token(token) is True
    assert auth.verify_token("invalid_token") is False
    assert auth.verify_token("") is False

    # Revoke token
    auth.revoke_token()
    assert not temp_token_file.exists()
    
    # get_token auto-generates if not exists
    new_token = auth.get_token()
    assert len(new_token) == 64
    assert temp_token_file.exists()
