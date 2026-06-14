"""Downloader for Shamkh reports from iccima.ir."""

import requests
from pathlib import Path
from pmi_analyzer.types import DownloadConfig
from pmi_analyzer.exceptions import DownloadError


class ICCIMADownloader:
    """Download Shamkh PDF reports from iccima.ir."""

    def __init__(self, config: DownloadConfig = None):
        self.config = config or DownloadConfig()

    def download_latest(self) -> Path:
        """
        Download the latest Shamkh report.

        Returns:
            Path to downloaded PDF

        Raises:
            DownloadError: If download fails
        """
        try:
            url = f"{self.config.base_url}/shamkh"
            response = requests.get(url, timeout=self.config.timeout)
            response.raise_for_status()

            self.config.output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self.config.output_dir / "shamkh_latest.pdf"

            with open(output_path, "wb") as f:
                f.write(response.content)

            return output_path

        except requests.RequestException as e:
            raise DownloadError(f"Download failed: {e}") from e
