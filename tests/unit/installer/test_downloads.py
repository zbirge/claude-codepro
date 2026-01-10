"""Tests for downloads module with httpx."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestDownloadConfig:
    """Test DownloadConfig class."""

    def test_download_config_stores_values(self):
        """DownloadConfig stores repository settings."""
        from installer.downloads import DownloadConfig

        config = DownloadConfig(
            repo_url="https://github.com/test/repo",
            repo_branch="main",
        )
        assert config.repo_url == "https://github.com/test/repo"
        assert config.repo_branch == "main"
        assert config.local_mode is False
        assert config.local_repo_dir is None

    def test_download_config_local_mode(self):
        """DownloadConfig supports local mode."""
        from installer.downloads import DownloadConfig

        config = DownloadConfig(
            repo_url="https://github.com/test/repo",
            repo_branch="main",
            local_mode=True,
            local_repo_dir=Path("/tmp/repo"),
        )
        assert config.local_mode is True
        assert config.local_repo_dir == Path("/tmp/repo")


class TestDownloadFile:
    """Test download_file function."""

    def test_download_file_creates_parent_dirs(self):
        """download_file creates parent directories."""
        from installer.downloads import DownloadConfig, download_file

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "subdir" / "file.txt"
            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=True,
                local_repo_dir=Path(tmpdir),
            )

            # Create source file
            source = Path(tmpdir) / "test.txt"
            source.write_text("test content")

            download_file("test.txt", dest, config)
            assert dest.parent.exists()

    def test_download_file_local_mode_copies(self):
        """download_file copies file in local mode."""
        from installer.downloads import DownloadConfig, download_file

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            source = source_dir / "test.txt"
            source.write_text("local content")

            dest = Path(tmpdir) / "dest" / "test.txt"
            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=True,
                local_repo_dir=source_dir,
            )

            result = download_file("test.txt", dest, config)
            assert result is True
            assert dest.exists()
            assert dest.read_text() == "local content"

    def test_download_file_returns_false_on_missing_source(self):
        """download_file returns False if source doesn't exist."""
        from installer.downloads import DownloadConfig, download_file

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "dest" / "test.txt"
            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=True,
                local_repo_dir=Path(tmpdir),
            )

            result = download_file("nonexistent.txt", dest, config)
            assert result is False


class TestVerifyNetwork:
    """Test verify_network function."""

    def test_verify_network_returns_bool(self):
        """verify_network returns a boolean."""
        from installer.downloads import verify_network

        result = verify_network()
        assert isinstance(result, bool)


class TestGetRepoFiles:
    """Test get_repo_files function."""

    def test_get_repo_files_local_mode(self):
        """get_repo_files returns files in local mode."""
        from installer.downloads import DownloadConfig, get_repo_files

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directory structure
            subdir = Path(tmpdir) / "mydir"
            subdir.mkdir()
            (subdir / "file1.txt").write_text("content1")
            (subdir / "file2.txt").write_text("content2")

            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=True,
                local_repo_dir=Path(tmpdir),
            )

            files = get_repo_files("mydir", config)
            assert len(files) == 2
            assert "mydir/file1.txt" in files
            assert "mydir/file2.txt" in files

    def test_get_repo_files_returns_empty_for_missing_dir(self):
        """get_repo_files returns empty list for missing directory."""
        from installer.downloads import DownloadConfig, get_repo_files

        with tempfile.TemporaryDirectory() as tmpdir:
            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=True,
                local_repo_dir=Path(tmpdir),
            )

            files = get_repo_files("nonexistent", config)
            assert files == []


class TestDownloadDirectory:
    """Test download_directory function."""

    def test_download_directory_local_mode(self):
        """download_directory copies directory in local mode."""
        from installer.downloads import DownloadConfig, download_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source directory
            source_dir = Path(tmpdir) / "source"
            subdir = source_dir / "mydir"
            subdir.mkdir(parents=True)
            (subdir / "file1.txt").write_text("content1")
            (subdir / "file2.txt").write_text("content2")

            dest_dir = Path(tmpdir) / "dest"
            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=True,
                local_repo_dir=source_dir,
            )

            count = download_directory("mydir", dest_dir, config)
            assert count == 2
            assert (dest_dir / "file1.txt").exists()
            assert (dest_dir / "file2.txt").exists()

    def test_download_directory_excludes_patterns(self):
        """download_directory respects exclude patterns."""
        from installer.downloads import DownloadConfig, download_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source directory
            source_dir = Path(tmpdir) / "source"
            subdir = source_dir / "mydir"
            subdir.mkdir(parents=True)
            (subdir / "file.txt").write_text("content")
            (subdir / "file.pyc").write_text("compiled")

            dest_dir = Path(tmpdir) / "dest"
            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=True,
                local_repo_dir=source_dir,
            )

            count = download_directory("mydir", dest_dir, config, exclude_patterns=["*.pyc"])
            assert count == 1
            assert (dest_dir / "file.txt").exists()
            assert not (dest_dir / "file.pyc").exists()

    def test_download_directory_with_progress_callback(self):
        """download_directory calls progress callback."""
        from installer.downloads import DownloadConfig, download_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            subdir = source_dir / "mydir"
            subdir.mkdir(parents=True)
            (subdir / "file1.txt").write_text("content1")
            (subdir / "file2.txt").write_text("content2")

            dest_dir = Path(tmpdir) / "dest"
            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=True,
                local_repo_dir=source_dir,
            )

            progress_calls = []

            def progress_cb(current, total):
                progress_calls.append((current, total))

            download_directory("mydir", dest_dir, config, progress_callback=progress_cb)

            # Should have been called for each file
            assert len(progress_calls) == 2


class TestVerifyNetworkBranches:
    """Test verify_network edge cases."""

    def test_verify_network_returns_false_on_http_error(self):
        """verify_network returns False on HTTP error."""
        import httpx

        from installer.downloads import verify_network

        with patch("installer.downloads.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.HTTPError("Error")

            result = verify_network()
            assert result is False

    def test_verify_network_returns_false_on_timeout(self):
        """verify_network returns False on timeout."""
        import httpx

        from installer.downloads import verify_network

        with patch("installer.downloads.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.TimeoutException("Timeout")

            result = verify_network()
            assert result is False

    def test_verify_network_returns_true_on_success(self):
        """verify_network returns True on 200 response."""
        from installer.downloads import verify_network

        with patch("installer.downloads.httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = verify_network()
            assert result is True


class TestDownloadFileHttpMode:
    """Test download_file HTTP mode."""

    def test_download_file_http_writes_content(self):
        """download_file writes content from HTTP response."""
        from installer.downloads import DownloadConfig, download_file

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "file.txt"
            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=False,
            )

            with patch("installer.downloads.httpx.Client") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.headers = {"content-length": "12"}
                mock_response.iter_bytes.return_value = [b"test content"]
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)

                mock_client.return_value.__enter__.return_value.stream.return_value = mock_response

                result = download_file("test.txt", dest, config)
                assert result is True
                assert dest.read_text() == "test content"

    def test_download_file_http_returns_false_on_404(self):
        """download_file returns False on 404 response."""
        from installer.downloads import DownloadConfig, download_file

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "file.txt"
            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=False,
            )

            with patch("installer.downloads.httpx.Client") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 404
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)

                mock_client.return_value.__enter__.return_value.stream.return_value = mock_response

                result = download_file("nonexistent.txt", dest, config)
                assert result is False

    def test_download_file_http_calls_progress_callback(self):
        """download_file calls progress callback."""
        from installer.downloads import DownloadConfig, download_file

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "file.txt"
            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=False,
            )

            progress_calls = []

            def progress_cb(downloaded, total):
                progress_calls.append((downloaded, total))

            with patch("installer.downloads.httpx.Client") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.headers = {"content-length": "24"}
                mock_response.iter_bytes.return_value = [b"part1", b"part2"]
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)

                mock_client.return_value.__enter__.return_value.stream.return_value = mock_response

                download_file("test.txt", dest, config, progress_callback=progress_cb)

                assert len(progress_calls) == 2

    def test_download_file_http_handles_network_error(self):
        """download_file returns False on network error."""
        import httpx

        from installer.downloads import DownloadConfig, download_file

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "file.txt"
            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=False,
            )

            with patch("installer.downloads.httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.stream.side_effect = httpx.HTTPError("Error")

                result = download_file("test.txt", dest, config)
                assert result is False


class TestDownloadFileLocalMode:
    """Test download_file local mode edge cases."""

    def test_download_file_local_mode_same_file(self):
        """download_file returns True when source equals dest."""
        from installer.downloads import DownloadConfig, download_file

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            file_path.write_text("content")

            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=True,
                local_repo_dir=Path(tmpdir),
            )

            # Use the same path for source and dest
            result = download_file("test.txt", file_path, config)
            assert result is True

    def test_download_file_local_mode_os_error(self):
        """download_file returns False on OSError."""
        from installer.downloads import DownloadConfig, download_file

        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source.txt"
            source.write_text("content")
            dest = Path(tmpdir) / "dest.txt"

            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=True,
                local_repo_dir=Path(tmpdir),
            )

            with patch("installer.downloads.shutil.copy2") as mock_copy:
                mock_copy.side_effect = OSError("Permission denied")

                result = download_file("source.txt", dest, config)
                assert result is False


class TestGetRepoFilesHttpMode:
    """Test get_repo_files HTTP mode."""

    def test_get_repo_files_http_parses_github_tree(self):
        """get_repo_files parses GitHub API tree response."""
        from installer.downloads import DownloadConfig, get_repo_files

        config = DownloadConfig(
            repo_url="https://github.com/test/repo",
            repo_branch="main",
            local_mode=False,
        )

        with patch("installer.downloads.httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "tree": [
                    {"type": "blob", "path": "mydir/file1.txt"},
                    {"type": "blob", "path": "mydir/file2.txt"},
                    {"type": "tree", "path": "mydir/subdir"},  # Should be ignored
                    {"type": "blob", "path": "other/file.txt"},  # Different dir
                ]
            }

            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            files = get_repo_files("mydir", config)

            assert len(files) == 2
            assert "mydir/file1.txt" in files
            assert "mydir/file2.txt" in files

    def test_get_repo_files_http_returns_empty_on_error(self):
        """get_repo_files returns empty list on HTTP error."""
        import httpx

        from installer.downloads import DownloadConfig, get_repo_files

        config = DownloadConfig(
            repo_url="https://github.com/test/repo",
            repo_branch="main",
            local_mode=False,
        )

        with patch("installer.downloads.httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.HTTPError("Error")

            files = get_repo_files("mydir", config)
            assert files == []

    def test_get_repo_files_http_returns_empty_on_non_200(self):
        """get_repo_files returns empty list on non-200 status."""
        from installer.downloads import DownloadConfig, get_repo_files

        config = DownloadConfig(
            repo_url="https://github.com/test/repo",
            repo_branch="main",
            local_mode=False,
        )

        with patch("installer.downloads.httpx.Client") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404

            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            files = get_repo_files("mydir", config)
            assert files == []


class TestDownloadWithRetry:
    """Test download_with_retry function."""

    def test_download_with_retry_succeeds_on_first_attempt(self):
        """download_with_retry succeeds on first attempt."""
        from installer.downloads import DownloadConfig, download_with_retry

        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "test.txt"
            source.write_text("content")
            dest = Path(tmpdir) / "dest" / "test.txt"

            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=True,
                local_repo_dir=Path(tmpdir),
            )

            result = download_with_retry("test.txt", dest, config)
            assert result is True
            assert dest.read_text() == "content"

    def test_download_with_retry_retries_on_failure(self):
        """download_with_retry retries on failure."""
        from installer.downloads import DownloadConfig, download_with_retry

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "dest" / "test.txt"

            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=True,
                local_repo_dir=Path(tmpdir),
            )

            call_count = 0

            def mock_download_file(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    return False
                return True

            with patch("installer.downloads.download_file", side_effect=mock_download_file):
                result = download_with_retry("test.txt", dest, config, max_retries=5)
                assert result is True
                assert call_count == 3

    def test_download_with_retry_returns_false_after_max_retries(self):
        """download_with_retry returns False after max retries."""
        from installer.downloads import DownloadConfig, download_with_retry

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = Path(tmpdir) / "dest" / "test.txt"

            config = DownloadConfig(
                repo_url="https://github.com/test/repo",
                repo_branch="main",
                local_mode=True,
                local_repo_dir=Path(tmpdir),
            )

            with patch("installer.downloads.download_file", return_value=False):
                result = download_with_retry("test.txt", dest, config, max_retries=3)
                assert result is False
