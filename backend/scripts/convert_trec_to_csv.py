"""
将 TREC 格式的垃圾邮件语料库（index + 原始邮件文件）转换为 CSV 格式，
以便导入到垃圾邮件分类系统中进行训练。

用法:
    cd backend
    python scripts/convert_trec_to_csv.py

输出: data/uploads/trec_spam_dataset.csv
"""

import os
import re
import csv
import email
import email.policy
from email import charset as email_charset
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_ROOT = BASE_DIR / "data" / "datasets" / "data"
INDEX_FILE = DATA_ROOT / "index"
OUTPUT_DIR = BASE_DIR / "data" / "uploads"
OUTPUT_FILE = OUTPUT_DIR / "trec_spam_dataset.csv"

ENCODINGS_TO_TRY = ["gb2312", "gbk", "gb18030", "utf-8", "latin-1"]


def read_file_with_fallback(file_path: Path) -> bytes:
    return file_path.read_bytes()


def extract_email_body(raw_bytes: bytes) -> str:
    """从原始邮件字节中提取纯文本正文。"""
    for enc in ENCODINGS_TO_TRY:
        try:
            raw_str = raw_bytes.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:
        raw_str = raw_bytes.decode("latin-1")

    try:
        msg = email.message_from_string(raw_str, policy=email.policy.compat32)
    except Exception:
        return _fallback_body_extraction(raw_str)

    parts_text = []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                payload = _decode_payload(part)
                if payload:
                    parts_text.append(payload)
            elif ctype == "text/html" and not parts_text:
                payload = _decode_payload(part)
                if payload:
                    parts_text.append(_strip_html(payload))
    else:
        payload = _decode_payload(msg)
        if payload:
            ctype = msg.get_content_type()
            if ctype == "text/html":
                parts_text.append(_strip_html(payload))
            else:
                parts_text.append(payload)

    body = "\n".join(parts_text).strip()
    if not body:
        body = _fallback_body_extraction(raw_str)

    return _clean_text(body)


def _decode_payload(part) -> str:
    """安全地解码邮件 part 的 payload。"""
    try:
        payload_bytes = part.get_payload(decode=True)
        if payload_bytes is None:
            return ""
        part_charset = part.get_content_charset() or "gb2312"
        for enc in [part_charset] + ENCODINGS_TO_TRY:
            try:
                return payload_bytes.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return payload_bytes.decode("latin-1")
    except Exception:
        raw = part.get_payload()
        return raw if isinstance(raw, str) else ""


def _fallback_body_extraction(raw_str: str) -> str:
    """当 email 解析失败时，用简单的 header/body 分割提取正文。"""
    parts = re.split(r"\n\s*\n", raw_str, maxsplit=1)
    if len(parts) > 1:
        return parts[1].strip()
    return raw_str.strip()


def _strip_html(html: str) -> str:
    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;?", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    return text


def _clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_index(index_path: Path) -> list[tuple[str, Path]]:
    """解析 index 文件，返回 [(label, file_path), ...]。"""
    entries = []
    with open(index_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            label, rel_path = parts
            rel_path = rel_path.lstrip("./").replace("/", os.sep)
            abs_path = DATA_ROOT / rel_path
            entries.append((label.lower(), abs_path))
    return entries


def main():
    print(f"读取索引文件: {INDEX_FILE}")
    entries = parse_index(INDEX_FILE)
    print(f"共找到 {len(entries)} 条记录")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success, failed = 0, 0
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["label", "text"])

        for i, (label, file_path) in enumerate(entries):
            if not file_path.exists():
                failed += 1
                continue
            try:
                raw = read_file_with_fallback(file_path)
                body = extract_email_body(raw)
                if len(body) < 5:
                    failed += 1
                    continue
                writer.writerow([label, body])
                success += 1
            except Exception as e:
                failed += 1
                if failed <= 5:
                    print(f"  [警告] 处理失败 {file_path}: {e}")

            if (i + 1) % 500 == 0:
                print(f"  已处理 {i + 1}/{len(entries)} ...")

    print(f"\n转换完成！")
    print(f"  成功: {success}")
    print(f"  失败: {failed}")
    print(f"  输出: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
