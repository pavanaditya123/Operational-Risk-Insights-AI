import unittest

from src.llm_risk_analyzer import is_retryable_gemini_error


class RetryableGeminiErrorTest(unittest.TestCase):
    def test_temporary_status_codes_are_retryable(self):
        for code in [429, 500, 502, 503, 504]:
            with self.subTest(code=code):
                error = type("FakeError", (), {"code": code})()

                self.assertTrue(is_retryable_gemini_error(error))

    def test_client_errors_are_not_retryable(self):
        error = type("FakeError", (), {"code": 400})()

        self.assertFalse(is_retryable_gemini_error(error))


if __name__ == "__main__":
    unittest.main()
