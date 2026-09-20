import re
from typing import Optional, Tuple, Dict, Any, List

THINKING_MODEL_PATTERNS = [
    "qwen3",
    "qwq",
    "deepseek-r1",
    "r1-distill",
    "thinking",
    "reasoner",
]

def is_thinking_model(model_id: Optional[str]) -> bool:
    if not model_id:
        return False
    lower = model_id.lower()
    return any(pat in lower for pat in THINKING_MODEL_PATTERNS)

def parse_thinking_content(text: str) -> Tuple[Optional[str], str]:
    if not text:
        return None, ""

    match = re.search(r"<(?:think|thinking)>(.*?)</(?:think|thinking)>", text, re.DOTALL)
    if match:
        reasoning = match.group(1).strip()
        content = (text[:match.start()] + text[match.end():]).strip()
        return (reasoning if reasoning else None, content)

    open_match = re.search(r"<(?:think|thinking)>(.*)", text, re.DOTALL)
    if open_match:
        reasoning = open_match.group(1).strip()
        content = text[:open_match.start()].strip()
        return (reasoning if reasoning else None, content)

    close_match = re.search(r"(.*?)</(?:think|thinking)>", text, re.DOTALL)
    if close_match:
        reasoning = close_match.group(1).strip()
        content = text[close_match.end():].strip()
        return (reasoning if reasoning else None, content)

    return None, text.strip()

class StreamingThinkingParser:
    def __init__(self, enable_thinking: bool = True):
        self.enable_thinking = enable_thinking
        self.in_reasoning = enable_thinking
        self.reasoning_closed = not enable_thinking
        self.emitted_reasoning = ""
        self.emitted_content = ""

    def process(self, current_text: str) -> List[Dict[str, str]]:
        if not self.enable_thinking:
            delta = current_text[len(self.emitted_content):]
            if delta:
                self.emitted_content = current_text
                return [{"content": delta}]
            return []

        cleaned = current_text
        for tag in ("<think>", "<thinking>"):
            if cleaned.startswith(tag):
                cleaned = cleaned[len(tag):]

        events: List[Dict[str, str]] = []

        if not self.reasoning_closed:
            end_tag = None
            end_idx = -1
            for tag in ("</think>", "</thinking>"):
                idx = cleaned.find(tag)
                if idx != -1:
                    if end_idx == -1 or idx < end_idx:
                        end_idx = idx
                        end_tag = tag

            if end_tag is not None:
                reasoning_part = cleaned[:end_idx]
                after_part = cleaned[end_idx + len(end_tag):].lstrip("\n")

                delta_reasoning = reasoning_part[len(self.emitted_reasoning):]
                if delta_reasoning:
                    events.append({"reasoning": delta_reasoning})
                    self.emitted_reasoning = reasoning_part

                self.reasoning_closed = True
                self.in_reasoning = False

                delta_content = after_part[len(self.emitted_content):]
                if delta_content:
                    events.append({"content": delta_content})
                    self.emitted_content = after_part
            else:
                delta_reasoning = cleaned[len(self.emitted_reasoning):]
                if delta_reasoning:
                    events.append({"reasoning": delta_reasoning})
                    self.emitted_reasoning = cleaned
        else:
            end_idx = -1
            end_tag = ""
            for tag in ("</think>", "</thinking>"):
                idx = cleaned.find(tag)
                if idx != -1:
                    end_idx = idx
                    end_tag = tag
                    break

            if end_idx != -1:
                after_part = cleaned[end_idx + len(end_tag):].lstrip("\n")
            else:
                after_part = cleaned

            delta_content = after_part[len(self.emitted_content):]
            if delta_content:
                events.append({"content": delta_content})
                self.emitted_content = after_part

        return events
