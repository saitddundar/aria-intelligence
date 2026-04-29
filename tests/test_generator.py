from src.llm.generator import QwenGenerator


def test_parse_json_direct():
    raw = '{"selected_indices": [1, 2], "explanation": "test"}'
    result = QwenGenerator._parse_json(raw)
    assert result == {"selected_indices": [1, 2], "explanation": "test"}


def test_parse_json_with_code_fence():
    raw = """Here is the result:
```json
{"selected_indices": [3, 5], "explanation": "good vibes"}
```
"""
    result = QwenGenerator._parse_json(raw)
    assert result["selected_indices"] == [3, 5]


def test_parse_json_with_surrounding_text():
    raw = 'I think these songs are great: {"selected_indices": [1], "explanation": "chill"} done.'
    result = QwenGenerator._parse_json(raw)
    assert result["selected_indices"] == [1]


def test_parse_json_invalid():
    result = QwenGenerator._parse_json("no json here at all")
    assert result is None
