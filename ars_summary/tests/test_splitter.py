#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_transcript import split_transcript


lines = [f"[00:{index // 60:02d}:{index % 60:02d}] 说话人{index % 4 + 1}：" + "测试内容" * 60 for index in range(360)]
chunks = split_transcript("\n".join(lines), target_size=9000, overlap_size=700)
assert len(chunks) >= 5, len(chunks)
assert chunks[0].startswith(lines[0])
for index, chunk in enumerate(chunks):
    assert len(chunk) < 11000, (index, len(chunk))
for previous, current in zip(chunks, chunks[1:]):
    assert previous.splitlines()[-1] in current
print(f"OK: {len(chunks)} chunks with sentence-boundary overlap")
