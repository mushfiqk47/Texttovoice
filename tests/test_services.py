import pytest
from backend.services import TTSService

class TestTTSService:
    def test_singleton_pattern(self):
        """Ensure only one instance exists."""
        s1 = TTSService()
        s2 = TTSService()
        assert s1 is s2
        
    def test_split_text_simple_sentences(self):
        """Test splitting simple sentences."""
        service = TTSService()
        text = "Hello world. This is a test. Another one!"
        # Use small max_chunk_len to force splitting for this test
        chunks = service._split_text(text, max_chunk_len=25)
        assert len(chunks) == 3
        assert chunks[0] == "Hello world."
        assert chunks[1] == "This is a test."
        assert chunks[2] == "Another one!"
        
    def test_split_text_respects_max_len(self):
        """Test that chunks are combined but respect max length."""
        service = TTSService()
        text = "Short one. " * 10
        # If max_len is large, they should be combined
        chunks = service._split_text(text, max_chunk_len=500)
        assert len(chunks) == 1
        
        # If max_len is small, they should be split
        chunks_small = service._split_text(text, max_chunk_len=20)
        # Each "Short one." is 10 chars. 
        # Logic is: combine if len(current) + len(next) < max.
        # 10 + 10 = 20. So < 20 is false. They won't combine.
        assert len(chunks_small) == 10

    def test_split_text_empty(self):
        """Test empty input."""
        service = TTSService()
        assert service._split_text("") == []
        assert service._split_text("   ") == []
