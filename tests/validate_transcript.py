#!/usr/bin/env python3
"""Offline verification of the Azure Speech JSON adapter used in the Dify Code node."""
import json
import sys
from pathlib import Path


def to_hms(milliseconds: float) -> str:
    total_seconds = max(0, int(float(milliseconds) / 1000))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def normalize(transcript_json: str, mapping_json: str) -> dict[str, str]:
    items = json.loads(transcript_json)
    if not isinstance(items, list):
        raise ValueError("Expected top-level array")
    mapping = json.loads(mapping_json)
    normalized = []
    speakers = {}
    invalid_count = 0
    for index, item in enumerate(items):
        content = str(item.get("content") or "").strip() if isinstance(item, dict) else ""
        speaker = item.get("speaker") or {} if isinstance(item, dict) else {}
        start_time = item.get("start_time") if isinstance(item, dict) else None
        end_time = item.get("end_time") if isinstance(item, dict) else None
        speaker_id = str(speaker.get("id") or "unknown")
        if not content or start_time is None or end_time is None:
            invalid_count += 1
            continue
        start_time, end_time = float(start_time), float(end_time)
        if start_time < 0 or end_time < start_time:
            invalid_count += 1
            continue
        source_name = str(speaker.get("name") or f"说话人{speaker_id}").strip()
        name = str(mapping.get(speaker_id) or source_name or f"说话人{speaker_id}").strip()
        speakers[speaker_id] = name
        normalized.append((start_time, end_time, index, name, content))
    if not normalized:
        raise ValueError("No valid sentences")
    normalized.sort(key=lambda row: (row[0], row[2]))
    transcript = "\n".join(f"[{to_hms(start)}] {name}：{text}" for start, _, _, name, text in normalized)
    return {
        "normalized_transcript": transcript,
        "meeting_metadata": json.dumps({
            "sentence_count": len(normalized),
            "skipped_invalid_records": invalid_count,
            "speaker_mapping": speakers,
            "start_time": to_hms(normalized[0][0]),
            "end_time": to_hms(normalized[-1][1]),
            "duration_minutes": round((normalized[-1][1] - normalized[0][0]) / 60000, 2),
        }, ensure_ascii=False),
    }


def split_transcript(text: str, target_size: int = 9000, overlap_size: int = 700) -> list[str]:
    lines = [line for line in text.splitlines() if line.strip()]
    chunks, current, current_size = [], [], 0
    for line in lines:
        line_size = len(line) + 1
        if current and current_size + line_size > target_size:
            chunks.append("\n".join(current))
            overlap, overlap_count = [], 0
            for previous in reversed(current):
                overlap.insert(0, previous)
                overlap_count += len(previous) + 1
                if overlap_count >= overlap_size:
                    break
            current = overlap
            current_size = sum(len(item) + 1 for item in current)
        current.append(line)
        current_size += line_size
    if current:
        chunks.append("\n".join(current))
    return chunks


if __name__ == "__main__":
    fixture = Path(__file__).parent / "fixtures" / "azure-speech-sample.json"
    result = normalize(fixture.read_text(encoding="utf-8"), '{"1":"面试官","2":"候选人"}')
    metadata = json.loads(result["meeting_metadata"])
    assert metadata["sentence_count"] == 82
    assert metadata["speaker_mapping"] == {"1": "面试官", "2": "候选人"}
    assert result["normalized_transcript"].startswith("[00:00:00] 面试官：那请你先简单做个自我介绍吧。")
    assert "[00:00:03] 候选人：好，面试官你好" in result["normalized_transcript"]
    chunks = split_transcript(result["normalized_transcript"])
    assert len(chunks) == 1
    print("OK: 82 sentences, 2 mapped speakers, ordered timestamps, 1 chunk")
