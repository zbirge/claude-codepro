"""Tests for ccp.auth module."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from ccp.auth import (
    GumroadLicenseVerifier,
    LicenseManager,
    LicenseResult,
    LicenseState,
    TamperedStateError,
    create_eval_state,
    create_free_tier_state,
    subscribe_to_gumroad,
)


class TestLicenseState:
    """Tests for LicenseState dataclass."""

    def test_license_state_to_dict(self):
        """LicenseState can be serialized to dict."""
        now = datetime.now(timezone.utc)
        state = LicenseState(
            license_key="TEST-KEY",
            tier="commercial",
            email="test@example.com",
            created_at=now,
        )
        d = state.to_dict()
        assert d["license_key"] == "TEST-KEY"
        assert d["tier"] == "commercial"
        assert d["email"] == "test@example.com"

    def test_license_state_from_dict(self):
        """LicenseState can be deserialized from dict."""
        now = datetime.now(timezone.utc)
        d = {
            "license_key": "TEST-KEY",
            "tier": "trial",
            "email": "test@example.com",
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(days=7)).isoformat(),
        }
        state = LicenseState.from_dict(d)
        assert state.license_key == "TEST-KEY"
        assert state.tier == "trial"
        assert state.email == "test@example.com"

    def test_is_trial_expired_false_for_free_tier(self):
        """Free tier never expires."""
        state = LicenseState(license_key="FREE", tier="free")
        assert state.is_trial_expired() is False

    def test_is_trial_expired_false_for_commercial(self):
        """Commercial tier never expires."""
        state = LicenseState(license_key="KEY", tier="commercial")
        assert state.is_trial_expired() is False

    def test_is_trial_expired_false_when_trial_active(self):
        """Trial not expired when within 7 days."""
        now = datetime.now(timezone.utc)
        state = LicenseState(
            license_key="TRIAL",
            tier="trial",
            expires_at=now + timedelta(days=3),
        )
        assert state.is_trial_expired() is False

    def test_is_trial_expired_true_when_trial_past(self):
        """Trial expired when past expiration date."""
        now = datetime.now(timezone.utc)
        state = LicenseState(
            license_key="TRIAL",
            tier="trial",
            expires_at=now - timedelta(days=1),
        )
        assert state.is_trial_expired() is True

    def test_days_remaining_for_trial(self):
        """days_remaining returns days left for trial."""
        now = datetime.now(timezone.utc)
        state = LicenseState(
            license_key="TRIAL",
            tier="trial",
            expires_at=now + timedelta(days=5),
        )
        days = state.days_remaining()
        assert 4 <= days <= 5

    def test_days_remaining_zero_when_expired(self):
        """days_remaining returns 0 when expired."""
        now = datetime.now(timezone.utc)
        state = LicenseState(
            license_key="TRIAL",
            tier="trial",
            expires_at=now - timedelta(days=1),
        )
        assert state.days_remaining() == 0

    def test_days_remaining_none_for_free(self):
        """days_remaining returns None for free tier."""
        state = LicenseState(license_key="FREE", tier="free")
        assert state.days_remaining() is None

    def test_days_remaining_none_for_commercial(self):
        """days_remaining returns None for commercial tier."""
        state = LicenseState(license_key="KEY", tier="commercial")
        assert state.days_remaining() is None


class TestGumroadLicenseVerifier:
    """Tests for GumroadLicenseVerifier."""

    @patch("ccp.auth.httpx.post")
    def test_verify_license_success(self, mock_post):
        """Successful verification returns LicenseResult with success=True."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "purchase": {"quantity": 2, "email": "test@example.com"},
            "uses": 1,
        }

        verifier = GumroadLicenseVerifier()
        result = verifier.verify_license("TEST-KEY")

        assert result.success is True
        assert result.seats_total == 2
        assert result.email == "test@example.com"

    @patch("ccp.auth.httpx.post")
    def test_verify_license_invalid_key(self, mock_post):
        """Invalid key returns LicenseResult with success=False."""
        mock_post.return_value.status_code = 404

        verifier = GumroadLicenseVerifier()
        result = verifier.verify_license("INVALID")

        assert result.success is False
        assert "Invalid" in result.error

    @patch("ccp.auth.httpx.post")
    def test_verify_license_refunded(self, mock_post):
        """Refunded license returns error."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "purchase": {"refunded": True},
        }

        verifier = GumroadLicenseVerifier()
        result = verifier.verify_license("TEST-KEY")

        assert result.success is False
        assert "refunded" in result.error.lower()

    @patch("ccp.auth.httpx.post")
    def test_verify_license_network_error(self, mock_post):
        """Network error returns LicenseResult with error."""
        mock_post.side_effect = Exception("Connection failed")

        verifier = GumroadLicenseVerifier()
        result = verifier.verify_license("TEST-KEY")

        assert result.success is False
        assert "Network error" in result.error


class TestSubscribeToGumroad:
    """Tests for subscribe_to_gumroad function."""

    @patch("ccp.auth.httpx.post")
    def test_subscribe_success(self, mock_post):
        """Successful subscription returns success=True."""
        mock_post.return_value.status_code = 200

        result = subscribe_to_gumroad("test@example.com")

        assert result.success is True

    @patch("ccp.auth.httpx.post")
    def test_subscribe_failure(self, mock_post):
        """Failed subscription returns success=False."""
        mock_post.return_value.status_code = 500

        result = subscribe_to_gumroad("test@example.com")

        assert result.success is False


class TestLicenseManager:
    """Tests for LicenseManager."""

    def test_activate_success(self, tmp_path):
        """Successful activation saves state."""
        mock_verifier = MagicMock()
        mock_verifier.verify_license.return_value = LicenseResult(
            success=True, seats_total=1, seats_used=1, email="test@example.com"
        )

        manager = LicenseManager(config_dir=tmp_path, verifier=mock_verifier)
        result = manager.activate("TEST-KEY")

        assert result.success is True
        assert result.tier == "commercial"

        state = manager.get_state()
        assert state is not None
        assert state.tier == "commercial"
        assert state.email == "test@example.com"

    def test_activate_failure(self, tmp_path):
        """Failed activation returns error."""
        mock_verifier = MagicMock()
        mock_verifier.verify_license.return_value = LicenseResult(success=False, error="Invalid key")

        manager = LicenseManager(config_dir=tmp_path, verifier=mock_verifier)
        result = manager.activate("INVALID")

        assert result.success is False
        assert "Invalid" in result.error

    def test_get_state_returns_none_when_no_license(self, tmp_path):
        """get_state returns None when no license file."""
        manager = LicenseManager(config_dir=tmp_path)
        assert manager.get_state() is None

    def test_deactivate_removes_state(self, tmp_path):
        """deactivate removes the license file."""
        manager = LicenseManager(config_dir=tmp_path)
        create_free_tier_state(config_dir=tmp_path, email="test@example.com")

        assert manager.get_state() is not None
        assert manager.deactivate() is True
        assert manager.get_state() is None

    def test_deactivate_returns_false_when_no_license(self, tmp_path):
        """deactivate returns False when no license."""
        manager = LicenseManager(config_dir=tmp_path)
        assert manager.deactivate() is False

    def test_get_license_info(self, tmp_path):
        """get_license_info returns tier, email, and date fields."""
        create_free_tier_state(config_dir=tmp_path, email="test@example.com")
        manager = LicenseManager(config_dir=tmp_path)

        info = manager.get_license_info()
        assert info is not None
        assert info["tier"] == "free"
        assert info["email"] == "test@example.com"
        assert info["days_remaining"] is None
        assert info["created_at"] is not None
        assert info["expires_at"] is None
        assert info["is_expired"] is False

    def test_get_license_info_trial(self, tmp_path):
        """get_license_info returns expiration info for trial."""
        create_eval_state(config_dir=tmp_path, email="trial@example.com")
        manager = LicenseManager(config_dir=tmp_path)

        info = manager.get_license_info()
        assert info is not None
        assert info["tier"] == "trial"
        assert info["email"] == "trial@example.com"
        assert info["days_remaining"] is not None
        assert info["created_at"] is not None
        assert info["expires_at"] is not None
        assert info["is_expired"] is False

    def test_tamper_detection(self, tmp_path):
        """Tampered state file raises error."""
        manager = LicenseManager(config_dir=tmp_path)
        create_free_tier_state(config_dir=tmp_path)

        license_file = tmp_path / ".license"
        content = license_file.read_text()
        license_file.write_text(content.replace("free", "commercial"))

        with pytest.raises(TamperedStateError):
            manager._load_state()


class TestCreateFreeTierState:
    """Tests for create_free_tier_state."""

    def test_creates_free_tier(self, tmp_path):
        """Creates a free tier state."""
        state = create_free_tier_state(config_dir=tmp_path, email="test@example.com")

        assert state.tier == "free"
        assert state.license_key == "FREE"
        assert state.email == "test@example.com"
        assert state.expires_at is None

    def test_state_is_persisted(self, tmp_path):
        """State is saved to disk."""
        create_free_tier_state(config_dir=tmp_path)

        manager = LicenseManager(config_dir=tmp_path)
        state = manager.get_state()

        assert state is not None
        assert state.tier == "free"


class TestCreateEvalState:
    """Tests for create_eval_state (trial)."""

    def test_creates_trial_tier(self, tmp_path):
        """Creates a trial tier state with 7-day expiration."""
        state = create_eval_state(config_dir=tmp_path, email="test@example.com")

        assert state.tier == "trial"
        assert state.license_key == "TRIAL"
        assert state.email == "test@example.com"
        assert state.expires_at is not None

    def test_trial_expires_in_7_days(self, tmp_path):
        """Trial expires approximately 7 days from creation."""
        state = create_eval_state(config_dir=tmp_path)

        days = state.days_remaining()
        assert days is not None
        assert 6 <= days <= 7

    def test_state_is_persisted(self, tmp_path):
        """State is saved to disk."""
        create_eval_state(config_dir=tmp_path)

        manager = LicenseManager(config_dir=tmp_path)
        state = manager.get_state()

        assert state is not None
        assert state.tier == "trial"


class TestLicenseValidation:
    """Tests for license validation and re-validation."""

    def test_validate_free_tier_always_valid(self, tmp_path):
        """Free tier license is always valid."""
        create_free_tier_state(config_dir=tmp_path)
        manager = LicenseManager(config_dir=tmp_path)

        is_valid, error = manager.validate()

        assert is_valid is True
        assert error == ""

    def test_validate_trial_not_expired(self, tmp_path):
        """Valid trial license passes validation."""
        create_eval_state(config_dir=tmp_path)
        manager = LicenseManager(config_dir=tmp_path)

        is_valid, error = manager.validate()

        assert is_valid is True
        assert error == ""

    def test_validate_trial_expired(self, tmp_path):
        """Expired trial license fails validation."""
        manager = LicenseManager(config_dir=tmp_path)
        # Manually create expired trial state
        state = LicenseState(
            license_key="TRIAL",
            tier="trial",
            created_at=datetime.now(timezone.utc) - timedelta(days=10),
            expires_at=datetime.now(timezone.utc) - timedelta(days=3),
        )
        manager._save_state(state)

        is_valid, error = manager.validate()

        assert is_valid is False
        assert "expired" in error.lower()

    def test_validate_no_license(self, tmp_path):
        """No license file fails validation."""
        manager = LicenseManager(config_dir=tmp_path)

        is_valid, error = manager.validate()

        assert is_valid is False
        assert "No license" in error

    def test_needs_revalidation_commercial_old(self, tmp_path):
        """Commercial license needs revalidation after 24 hours."""
        state = LicenseState(
            license_key="COMMERCIAL-KEY",
            tier="commercial",
            last_validated_at=datetime.now(timezone.utc) - timedelta(hours=25),
        )

        assert state.needs_revalidation() is True

    def test_needs_revalidation_commercial_recent(self, tmp_path):
        """Commercial license doesn't need revalidation within 24 hours."""
        state = LicenseState(
            license_key="COMMERCIAL-KEY",
            tier="commercial",
            last_validated_at=datetime.now(timezone.utc) - timedelta(hours=12),
        )

        assert state.needs_revalidation() is False

    def test_needs_revalidation_free_tier(self):
        """Free tier never needs revalidation."""
        state = LicenseState(license_key="FREE", tier="free")

        assert state.needs_revalidation() is False

    def test_validate_commercial_revalidates_with_gumroad(self, tmp_path):
        """Commercial license re-validates with Gumroad API when needed."""
        mock_verifier = MagicMock()
        mock_verifier.verify_license.return_value = LicenseResult(success=True)

        manager = LicenseManager(config_dir=tmp_path, verifier=mock_verifier)

        # Create commercial state that needs revalidation
        state = LicenseState(
            license_key="COMMERCIAL-KEY",
            tier="commercial",
            last_validated_at=datetime.now(timezone.utc) - timedelta(hours=25),
        )
        manager._save_state(state)

        is_valid, error = manager.validate()

        assert is_valid is True
        mock_verifier.verify_license.assert_called_once_with("COMMERCIAL-KEY", increment_uses=False)

    def test_validate_commercial_subscription_cancelled(self, tmp_path):
        """Commercial license fails when subscription is cancelled."""
        mock_verifier = MagicMock()
        mock_verifier.verify_license.return_value = LicenseResult(
            success=False, error="Subscription has been cancelled"
        )

        manager = LicenseManager(config_dir=tmp_path, verifier=mock_verifier)

        # Create commercial state that needs revalidation
        state = LicenseState(
            license_key="COMMERCIAL-KEY",
            tier="commercial",
            last_validated_at=datetime.now(timezone.utc) - timedelta(hours=25),
        )
        manager._save_state(state)

        is_valid, error = manager.validate()

        assert is_valid is False
        assert "cancelled" in error.lower()
        # License file should be removed
        assert manager.get_state() is None
