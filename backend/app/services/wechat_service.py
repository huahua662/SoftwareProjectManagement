import json
import csv
import io
from typing import List, Dict, Any
from datetime import datetime


class WechatService:
    """Parse WeChat chat exports from PyWxDump or generic formats."""

    def parse_pywxdump_json(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        records = []
        for item in data:
            msg_type = "text"
            content = item.get("content", "") or item.get("msg", "")
            type_id = item.get("type", 1)
            if type_id == 3:
                msg_type = "image"
            elif type_id == 34:
                msg_type = "voice"
            elif type_id == 43:
                msg_type = "video"

            ts = None
            if item.get("timestamp"):
                try:
                    ts = datetime.fromtimestamp(int(item["timestamp"]))
                except (ValueError, TypeError, OSError):
                    pass
            elif item.get("createTime"):
                try:
                    ts = datetime.fromtimestamp(int(item["createTime"]))
                except (ValueError, TypeError, OSError):
                    pass

            records.append({
                "sender": item.get("sender", item.get("talker", "")),
                "content": content,
                "msg_type": msg_type,
                "timestamp": ts.isoformat() if ts else None,
            })
        return records

    def parse_txt(self, text: str) -> List[Dict[str, Any]]:
        records = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            if ": " in line:
                sender, content = line.split(": ", 1)
            else:
                sender, content = "", line
            records.append({
                "sender": sender,
                "content": content,
                "msg_type": "text",
                "timestamp": None,
            })
        return records

    def parse_csv(self, text: str) -> List[Dict[str, Any]]:
        records = []
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            records.append({
                "sender": row.get("sender", ""),
                "content": row.get("content", ""),
                "msg_type": row.get("msg_type", "text"),
                "timestamp": row.get("timestamp"),
            })
        return records
