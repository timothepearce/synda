import unittest
from unittest.mock import patch, MagicMock

from synda.utils.llm_provider import LLMProvider


class TestLLMProvider(unittest.TestCase):
    @patch("synda.utils.llm_provider.completion")
    def test_openrouter_provider_resolution(self, mock_completion):
        # Setup mock
        mock_completion.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        
        # Call the provider with openrouter
        LLMProvider.call(
            provider="openrouter",
            model="openai/gpt-3.5-turbo",
            api_key="test_key",
            prompt="Test prompt",
            temperature=0.7,
        )
        
        # Check that the provider was correctly resolved
        mock_completion.assert_called_once()
        args, kwargs = mock_completion.call_args
        
        # Verify the model name was correctly formatted with the provider
        self.assertEqual(kwargs["model"], "openrouter/openai/gpt-3.5-turbo")
        
        # Verify other parameters
        self.assertEqual(kwargs["api_key"], "test_key")
        self.assertEqual(kwargs["messages"][0]["content"], "Test prompt")
        self.assertEqual(kwargs["temperature"], 0.7)


if __name__ == "__main__":
    unittest.main()