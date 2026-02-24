"""Tests for the NHI (Non-Human Identity) cryptographic signing layer."""

import copy

import pytest

from ecoverify.nhi.keys import generate_agent_keypair, load_private_key, load_public_key, get_public_key_b64
from ecoverify.nhi.signing import sign_decision_trace, verify_decision_trace, DecisionTrace
from ecoverify.nhi.middleware import cite_data_source, verify_citations_present, verify_citation_against_data


class TestKeyGeneration:
    """Ed25519 key generation and persistence."""

    def test_generate_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ecoverify.config.settings.keys_dir", str(tmp_path))
        pk, pub = generate_agent_keypair("test_agent")
        assert pk is not None
        assert pub is not None

        loaded_pk = load_private_key("test_agent")
        assert loaded_pk is not None

        loaded_pub = load_public_key("test_agent")
        assert loaded_pub is not None

    def test_idempotent_generation(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ecoverify.config.settings.keys_dir", str(tmp_path))
        pk1, _ = generate_agent_keypair("test_agent")
        pk2, _ = generate_agent_keypair("test_agent")  # should load, not regenerate
        # Both should produce the same public key
        pub1 = pk1.public_key().public_bytes_raw()
        pub2 = pk2.public_key().public_bytes_raw()
        assert pub1 == pub2

    def test_public_key_b64(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ecoverify.config.settings.keys_dir", str(tmp_path))
        generate_agent_keypair("test_agent")
        b64 = get_public_key_b64("test_agent")
        assert isinstance(b64, str)
        assert len(b64) == 44  # 32 bytes → 44 chars base64

    def test_missing_key_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ecoverify.config.settings.keys_dir", str(tmp_path))
        with pytest.raises(FileNotFoundError):
            load_private_key("nonexistent_agent")


class TestDecisionSigning:
    """Ed25519 signing and verification of decision traces."""

    def test_sign_and_verify(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ecoverify.config.settings.keys_dir", str(tmp_path))
        pk, pub = generate_agent_keypair("test_agent")

        decision = {"action": "test", "value": 42, "nested": {"key": "val"}}
        trace = sign_decision_trace("test_agent", decision, pk)

        assert trace.agent_id == "test_agent"
        assert trace.payload_hash
        assert trace.signature
        assert len(trace.payload_hash) == 64  # SHA-256 hex digest
        assert verify_decision_trace(trace, pub) is True

    def test_tampered_decision_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ecoverify.config.settings.keys_dir", str(tmp_path))
        pk, pub = generate_agent_keypair("test_agent")

        trace = sign_decision_trace("test_agent", {"action": "original"}, pk)
        assert verify_decision_trace(trace, pub) is True

        # Tamper with the decision
        tampered = trace.model_copy()
        tampered.decision = {"action": "tampered"}
        assert verify_decision_trace(tampered, pub) is False

    def test_tampered_signature_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ecoverify.config.settings.keys_dir", str(tmp_path))
        pk, pub = generate_agent_keypair("test_agent")

        trace = sign_decision_trace("test_agent", {"action": "test"}, pk)

        # Flip a character in the signature
        tampered = trace.model_copy()
        sig_list = list(tampered.signature)
        sig_list[5] = "X" if sig_list[5] != "X" else "Y"
        tampered.signature = "".join(sig_list)
        assert verify_decision_trace(tampered, pub) is False

    def test_wrong_key_fails(self, tmp_path, monkeypatch):
        monkeypatch.setattr("ecoverify.config.settings.keys_dir", str(tmp_path))
        pk1, _ = generate_agent_keypair("agent_1")
        pk2, pub2 = generate_agent_keypair("agent_2", overwrite=True)

        trace = sign_decision_trace("agent_1", {"action": "test"}, pk1)
        # Verify with wrong public key
        assert verify_decision_trace(trace, pub2) is False


class TestCiteBeforeAct:
    """Cite-Before-Act middleware — citation creation and verification."""

    def test_cite_dict_data(self):
        citation = cite_data_source("bms:energy:HQ-01", {"readings": [1, 2, 3]})
        assert citation.source_id == "bms:energy:HQ-01"
        assert len(citation.data_hash) == 64
        assert citation.timestamp

    def test_cite_string_data(self):
        citation = cite_data_source("report:123", "some raw text data")
        assert citation.data_hash
        assert len(citation.data_hash) == 64

    def test_verify_citations_present(self):
        citation = cite_data_source("src", {"data": True})
        assert verify_citations_present([citation]) is True
        assert verify_citations_present([]) is False

    def test_verify_citation_against_data(self):
        data = {"readings": [10, 20, 30], "building": "HQ-01"}
        citation = cite_data_source("bms:energy", data)

        assert verify_citation_against_data(citation, data) is True
        assert verify_citation_against_data(citation, {"readings": [99]}) is False

    def test_snippet_truncation(self):
        long_snippet = "x" * 500
        citation = cite_data_source("src", "data", snippet=long_snippet)
        assert len(citation.snippet) == 200
