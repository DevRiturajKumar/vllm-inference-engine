import pytest
from app.thinking import (
    is_thinking_model,
    parse_thinking_content,
    StreamingThinkingParser,
)

def test_is_thinking_model():
    assert is_thinking_model("Qwen/QwQ-32B") is True
    assert is_thinking_model("deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B") is True
    assert is_thinking_model("Qwen/Qwen3-8B") is True
    assert is_thinking_model("deepseek-ai/DeepSeek-V3") is False
    assert is_thinking_model("meta-llama/Llama-3.2-3B-Instruct") is False
    assert is_thinking_model(None) is False
    assert is_thinking_model("") is False

def test_parse_thinking_content_standard():
    text = "<think>Step 1: 2+2=4\nStep 2: Done</think>The answer is 4."
    reasoning, content = parse_thinking_content(text)
    assert reasoning == "Step 1: 2+2=4\nStep 2: Done"
    assert content == "The answer is 4."

def test_parse_thinking_content_alt_tag():
    text = "<thinking>Analysis here</thinking>Final answer."
    reasoning, content = parse_thinking_content(text)
    assert reasoning == "Analysis here"
    assert content == "Final answer."

def test_parse_thinking_content_unclosed():
    text = "<think>Still reasoning"
    reasoning, content = parse_thinking_content(text)
    assert reasoning == "Still reasoning"
    assert content == ""

def test_parse_thinking_content_no_thinking():
    text = "Just a direct response."
    reasoning, content = parse_thinking_content(text)
    assert reasoning is None
    assert content == "Just a direct response."

def test_parse_thinking_content_empty():
    reasoning, content = parse_thinking_content("")
    assert reasoning is None
    assert content == ""

def test_streaming_thinking_parser_enabled():
    parser = StreamingThinkingParser(enable_thinking=True)
    events1 = parser.process("<think>thinking 1")
    assert len(events1) == 1
    assert events1[0] == {"reasoning": "thinking 1"}

    events2 = parser.process("<think>thinking 1 thinking 2</think>Hello")
    assert any("reasoning" in e for e in events2)
    assert any("content" in e for e in events2)

    events3 = parser.process("<think>thinking 1 thinking 2</think>Hello world")
    assert len(events3) == 1
    assert events3[0] == {"content": " world"}

def test_streaming_thinking_parser_standard_model_not_trapped():
    # Model like Qwen 2.5 generating direct output without <think> tags
    parser = StreamingThinkingParser(enable_thinking=True, prompt_has_thinking_open=False)
    events1 = parser.process("Hello! ")
    assert len(events1) == 1
    assert events1[0] == {"content": "Hello! "}

    events2 = parser.process("Hello! How can I help you?")
    assert len(events2) == 1
    assert events2[0] == {"content": "How can I help you?"}

def test_streaming_thinking_parser_prefilled_prompt():
    # Prompt prefilled with <think>, so generated text starts in reasoning
    parser = StreamingThinkingParser(enable_thinking=True, prompt_has_thinking_open=True)
    events1 = parser.process("Calculating step 1... ")
    assert len(events1) == 1
    assert events1[0] == {"reasoning": "Calculating step 1... "}

    events2 = parser.process("Calculating step 1... </think>\nAnswer is 42.")
    assert any("content" in e for e in events2)

def test_streaming_thinking_parser_disabled():
    parser = StreamingThinkingParser(enable_thinking=False)
    events = parser.process("Normal response here")
    assert len(events) == 1
    assert events[0] == {"content": "Normal response here"}
