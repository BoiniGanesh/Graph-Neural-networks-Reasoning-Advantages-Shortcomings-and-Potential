from pathlib import Path
import requests
import pandas as pd
import logging


class PrimeKGDownloader:
    """
    Downloads and prepares PrimeKG dataset files from Harvard Dataverse.
    """

    def __init__(self, doi: str = "10.7910/DVN/IXA7BM", subfolder: str = "primekg"):
        """
        Initialize downloader settings including data paths and logging.

        :param doi: Dataverse DOI to download from
        :param subfolder: Subfolder to save downloaded files
        """
        self.dataset_doi = doi
        self.api_url = (
            f"https://dataverse.harvard.edu/api/datasets/:persistentId/versions/:latest/files"
            f"?persistentId=doi:{self.dataset_doi}"
        )
        self.chunk_size = 1024 * 1024  # 1MB chunk size for efficient streaming
        self.headers = {"User-Agent": "PrimeKGDownloader/1.0"}

        # Set up destination and logging directories
        self.root_dir = Path(__file__).resolve().parent.parent
        self.dest_dir = self.root_dir / "data" / subfolder
        self.dest_dir.mkdir(parents=True, exist_ok=True)

        log_dir = self.root_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{subfolder}_download.log"

        # Configure logging to file + console
        self.logger = logging.getLogger("PrimeKGDownloader")
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def fetch_file_list(self):
        """
        Use the Dataverse API to retrieve a list of available files.

        :return: List of file metadata dictionaries
        """
        self.logger.info(f"Fetching file list for DOI: {self.dataset_doi}")
        response = requests.get(self.api_url, headers=self.headers)
        response.raise_for_status()
        files = response.json().get("data", [])
        self.logger.info(f"Found {len(files)} files.")
        return files

    def download_file(self, file_info: dict) -> bool:
        """
        Download an individual file if it doesn't already exist and pass integrity check.

        :param file_info: Dictionary from the API describing the file
        :return: True if file is saved or already exists, False otherwise
        """
        label = file_info.get("label", "UNKNOWN")
        file_id = file_info.get("dataFile", {}).get("id")
        expected_size = file_info.get("size", None)

        if not file_id:
            self.logger.warning(f"Skipping {label} - no file ID.")
            return False

        save_path = self.dest_dir / label

        # Skip download if valid file already exists
        if save_path.exists() and expected_size and expected_size > 0:
            actual_size = save_path.stat().st_size
            if actual_size == expected_size:
                self.logger.info(f"{label} already exists and size matches. Skipping.")
                return True
            else:
                self.logger.warning(f"{label} exists but size mismatch. Re-downloading.")

        temp_path = save_path.with_suffix(".tmp")
        url = f"https://dataverse.harvard.edu/api/access/datafile/{file_id}"

        try:
            self.logger.info(f"Downloading {label}...")
            with requests.get(url, stream=True, headers=self.headers) as response:
                response.raise_for_status()

                # If HTML content, something is wrong (e.g., error page)
                content_type = response.headers.get("Content-Type", "")
                if "html" in content_type:
                    raise ValueError(f"Unexpected content type (HTML) received for {label}.")

                # Stream download to temporary file
                with open(temp_path, "wb") as out_file:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        out_file.write(chunk)

            # If size is known, validate
            downloaded_size = temp_path.stat().st_size
            if expected_size and expected_size > 0 and downloaded_size != expected_size:
                self.logger.error(
                    f"Size mismatch for {label}: expected {expected_size}, got {downloaded_size}."
                )
                temp_path.unlink(missing_ok=True)
                return False

            # Rename only if all checks pass
            temp_path.rename(save_path)
            self.logger.info(f"Saved {label} to {save_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to download {label}: {e}")
            temp_path.unlink(missing_ok=True)
            return False

    def convert_tab_to_csv(self):
        """
        Converts downloaded `.tab` files to `.csv` and deletes the originals.
        """
        self.logger.info("Converting .tab files to .csv...")
        for tab_file in self.dest_dir.glob("*.tab"):
            csv_file = tab_file.with_suffix(".csv")
            if csv_file.exists():
                self.logger.info(f"{csv_file.name} already exists. Skipping.")
                continue
            try:
                df = pd.read_csv(tab_file, sep="\t")
                df.to_csv(csv_file, index=False)
                tab_file.unlink()
                self.logger.info(f"Converted {tab_file.name} → {csv_file.name}")
            except Exception as e:
                self.logger.error(f"Failed to convert {tab_file.name}: {e}")

    def run(self) -> dict:
        """
        Run the full download pipeline and return paths for all processed files.

        :return: Dict of {filename: absolute_path or None if failed}
        """
        self.logger.info("=== Starting PrimeKG Download Session ===")
        files = self.fetch_file_list()
        results = {}

        for file_info in files:
            label = file_info.get("label", "UNKNOWN")
            success = self.download_file(file_info)
            path = str(self.dest_dir / label) if success else None
            results[label] = path

        self.convert_tab_to_csv()
        self.logger.info(f"All files stored in: {self.dest_dir.resolve()}")
        self.logger.info("=== Session Complete ===")
        return results


if __name__ == "__main__":
    downloader = PrimeKGDownloader()
    downloader.run()
    print(f"Download complete. Files saved in: {downloader.dest_dir.resolve()}")
