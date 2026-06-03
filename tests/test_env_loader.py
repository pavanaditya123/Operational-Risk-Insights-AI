import os
import tempfile
import unittest
from pathlib import Path

from src.llm_risk_analyzer import load_env_file


class EnvLoaderTest(unittest.TestCase):
    def test_load_env_file_sets_missing_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "GEMINI_API_KEY=test-key",
                        "GEMINI_MODEL='gemini-test-model'",
                        "# ignored comment",
                    ]
                ),
                encoding="utf-8",
            )

            original_key = os.environ.pop("GEMINI_API_KEY", None)
            original_model = os.environ.pop("GEMINI_MODEL", None)
            try:
                load_env_file(env_path)

                self.assertEqual(os.environ["GEMINI_API_KEY"], "test-key")
                self.assertEqual(os.environ["GEMINI_MODEL"], "gemini-test-model")
            finally:
                os.environ.pop("GEMINI_API_KEY", None)
                os.environ.pop("GEMINI_MODEL", None)
                if original_key is not None:
                    os.environ["GEMINI_API_KEY"] = original_key
                if original_model is not None:
                    os.environ["GEMINI_MODEL"] = original_model

    def test_load_env_file_does_not_override_existing_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("GEMINI_API_KEY=file-key", encoding="utf-8")

            original_key = os.environ.get("GEMINI_API_KEY")
            os.environ["GEMINI_API_KEY"] = "existing-key"
            try:
                load_env_file(env_path)

                self.assertEqual(os.environ["GEMINI_API_KEY"], "existing-key")
            finally:
                if original_key is None:
                    os.environ.pop("GEMINI_API_KEY", None)
                else:
                    os.environ["GEMINI_API_KEY"] = original_key


if __name__ == "__main__":
    unittest.main()
