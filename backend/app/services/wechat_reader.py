import ctypes
import ctypes.wintypes as wt
import base64
import io
import json
import time
from typing import Optional, List, Dict

import pyautogui
from PIL import Image

from app.services.ai_service import AIService


class WechatReaderService:
    """Read WeChat chat window via screenshot + AI vision."""

    WECHAT_CLASSES = [
        "Qt51514QWindowIcon",  # WeChat 4.x (Qt)
        "WeChatMainWndForPC",  # WeChat 3.x
    ]

    def find_wechat_window(self) -> Optional[Dict]:
        FindWindowW = ctypes.windll.user32.FindWindowW
        GetWindowRect = ctypes.windll.user32.GetWindowRect
        IsWindowVisible = ctypes.windll.user32.IsWindowVisible

        for cls in self.WECHAT_CLASSES:
            hwnd = FindWindowW(cls, None)
            if hwnd and IsWindowVisible(hwnd):
                rect = wt.RECT()
                GetWindowRect(hwnd, ctypes.byref(rect))
                return {
                    "hwnd": hwnd,
                    "class": cls,
                    "rect": {
                        "left": rect.left,
                        "top": rect.top,
                        "right": rect.right,
                        "bottom": rect.bottom,
                        "width": rect.right - rect.left,
                        "height": rect.bottom - rect.top,
                    },
                }
        return None

    def bring_to_front(self, hwnd: int):
        SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow
        ShowWindow = ctypes.windll.user32.ShowWindow
        SW_RESTORE = 9
        ShowWindow(hwnd, SW_RESTORE)
        SetForegroundWindow(hwnd)
        time.sleep(0.5)

    def capture_chat_area(self, hwnd: int) -> Image.Image:
        """Capture the WeChat window screenshot."""
        self.bring_to_front(hwnd)

        # Re-read the rect after bringing to front
        GetWindowRect = ctypes.windll.user32.GetWindowRect
        rect = wt.RECT()
        GetWindowRect(hwnd, ctypes.byref(rect))

        # Capture the window region
        screenshot = pyautogui.screenshot(region=(
            rect.left, rect.top,
            rect.right - rect.left,
            rect.bottom - rect.top,
        ))
        return screenshot

    def image_to_base64(self, img: Image.Image) -> str:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    async def extract_messages(self, img: Image.Image) -> List[Dict]:
        """Send screenshot to AI vision to extract chat messages."""
        ai = AIService()
        b64 = self.image_to_base64(img)

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个微信聊天记录识别助手。用户会给你一张微信聊天窗口的截图，"
                    "请你识别出所有聊天消息，提取每条消息的发送者和内容。\n"
                    "对于语音消息，如果截图中有转文字的内容也请提取。\n"
                    "请以JSON数组格式返回，每个元素包含 sender 和 content 字段：\n"
                    '[{"sender": "发送者名称", "content": "消息内容"}, ...]\n'
                    "注意：\n"
                    "- 只输出JSON数组，不要输出其他内容\n"
                    "- 如果是语音消息且未转文字，content填写[语音消息]\n"
                    "- 保持消息的原始顺序\n"
                    "- 忽略系统提示、时间戳等非聊天内容"
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请识别这张微信聊天截图中的所有消息："},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                ],
            },
        ]

        result = await ai.chat_json(messages, temperature=0.1, max_tokens=4096)
        if isinstance(result, list):
            return result
        return result.get("messages", result.get("records", []))

    async def read_and_extract(self) -> Dict:
        """Full flow: find window -> screenshot -> AI extract."""
        info = self.find_wechat_window()
        if not info:
            return {"error": "未找到微信窗口，请确保微信已打开且未最小化"}

        img = self.capture_chat_area(info["hwnd"])

        # Save screenshot for reference
        import os
        from app.config import settings
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        screenshot_path = os.path.join(settings.UPLOAD_DIR, "wechat_capture.png")
        img.save(screenshot_path)

        messages = await self.extract_messages(img)
        return {
            "messages": messages,
            "screenshot": screenshot_path,
            "window": info["rect"],
        }

    async def scroll_and_read(self, scroll_times: int = 0) -> Dict:
        """Read with optional scrolling to capture more messages."""
        info = self.find_wechat_window()
        if not info:
            return {"error": "未找到微信窗口，请确保微信已打开且未最小化"}

        self.bring_to_front(info["hwnd"])
        rect = info["rect"]

        all_messages = []

        # Scroll up first to get earlier messages
        if scroll_times > 0:
            center_x = rect["left"] + rect["width"] // 2
            center_y = rect["top"] + rect["height"] // 2
            pyautogui.click(center_x, center_y)
            time.sleep(0.3)
            for _ in range(scroll_times):
                pyautogui.scroll(5)  # scroll up
                time.sleep(0.5)

        # Capture current view
        img = self.capture_chat_area(info["hwnd"])

        import os
        from app.config import settings
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        screenshot_path = os.path.join(settings.UPLOAD_DIR, "wechat_capture.png")
        img.save(screenshot_path)

        messages = await self.extract_messages(img)
        return {
            "messages": messages,
            "screenshot": screenshot_path,
            "window": info["rect"],
        }
