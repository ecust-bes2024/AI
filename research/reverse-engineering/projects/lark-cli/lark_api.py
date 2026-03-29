"""
Lark API client — authentication, messaging, search.
Merged from LarkAgentX: auth.py, lark_client.py, header.py, params.py.
"""
import re
import time
from http.cookies import SimpleCookie

import requests

from lark_utils import generate_request_id, generate_long_request_id, generate_access_key
from lark_proto import (
    build_send_message_proto,
    build_search_proto,
    decode_search_response,
    build_create_chat_proto,
    decode_create_chat_response,
    build_get_user_name_proto,
    decode_user_name_response,
    build_get_group_name_proto,
    decode_group_name_response,
)

BASE_URL = "https://internal-api-lark-api.feishu.cn/im/gateway/"
CSRF_URL = "https://internal-api-lark-api.feishu.cn/accounts/csrf"
USER_INFO_URL = "https://internal-api-lark-api.feishu.cn/accounts/web/user"
WS_URL = "wss://msg-frontier.feishu.cn/ws/v2"
MESSENGER_URL = "https://open-dev.feishu.cn/messenger/"
TICKET_URL = "https://login.feishu.cn/suite/passport/frontier_ticket/"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0"
)


def _common_headers():
    return {
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "origin": "https://open-dev.feishu.cn",
        "referer": "https://open-dev.feishu.cn/",
        "sec-ch-ua": '"Microsoft Edge";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": UA,
    }


def _proto_headers(cmd, cmd_version="2.7.0"):
    h = _common_headers()
    h.update({
        "accept": "*/*",
        "content-type": "application/x-protobuf",
        "locale": "zh_CN",
        "priority": "u=1, i",
        "x-appid": "161471",
        "x-command": str(cmd),
        "x-command-version": cmd_version,
        "x-lgw-os-type": "1",
        "x-lgw-terminal-type": "2",
        "x-request-id": generate_request_id(),
        "x-source": "web",
        "x-web-version": "3.9.32",
    })
    return h


class LarkAPI:
    def __init__(self, cookie_str):
        self.cookie = self._parse_cookie(cookie_str)
        self.csrf_token = self._fetch_csrf_token()
        self.me_id = self._fetch_me_id()

    @staticmethod
    def _parse_cookie(cookie_str):
        sc = SimpleCookie()
        sc.load(cookie_str)
        return {k: v.value for k, v in sc.items()}

    def _fetch_csrf_token(self):
        h = _common_headers()
        h.update({
            "accept": "application/json, text/plain, */*",
            "cache-control": "no-cache",
            "priority": "u=1, i",
            "x-api-version": "1.0.8",
            "x-app-id": "12",
            "x-device-info": "platform=websdk",
            "x-lgw-os-type": "1",
            "x-lgw-terminal-type": "2",
            "x-request-id": generate_request_id(),
            "x-terminal-type": "2",
        })
        params = {"_t": str(int(time.time() * 1000))}
        resp = requests.post(CSRF_URL, headers=h, cookies=self.cookie, params=params)
        resp.raise_for_status()
        token = resp.cookies.get("swp_csrf_token")
        if not token:
            raise RuntimeError("Failed to obtain swp_csrf_token from response")
        return token

    def _fetch_me_id(self):
        h = _common_headers()
        h.update({
            "accept": "application/json, text/plain, */*",
            "cache-control": "no-cache",
            "priority": "u=1, i",
            "x-api-version": "1.0.8",
            "x-app-id": "12",
            "x-csrf-token": self.csrf_token,
            "x-device-info": "platform=websdk",
            "x-lgw-os-type": "1",
            "x-lgw-terminal-type": "2",
            "x-locale": "zh-CN",
            "x-request-id": generate_long_request_id(),
            "x-terminal-type": "2",
        })
        params = {"app_id": "12", "_t": str(int(time.time() * 1000))}
        resp = requests.get(USER_INFO_URL, headers=h, cookies=self.cookie, params=params)
        resp.raise_for_status()
        data = resp.json()
        user = data["data"]["user"]
        self.me_name = user.get("name", "")
        return str(user["id"])

    # ── public API ────────────────────────────────────────────

    def get_me(self):
        """Return current user id and name."""
        return {"user_id": self.me_id, "user_name": self.me_name}

    def search(self, query):
        """Search users/groups. Returns list of {type, id, title}."""
        h = _proto_headers(cmd=11021)
        pkt = build_search_proto(h["x-request-id"], query)
        resp = requests.post(BASE_URL, headers=h, cookies=self.cookie, data=pkt.SerializeToString())
        resp.raise_for_status()
        return decode_search_response(resp.content)

    def create_chat(self, user_id):
        """Create/get P2P chat with a user. Returns chat_id str."""
        h = _proto_headers(cmd=13)
        pkt = build_create_chat_proto(h["x-request-id"], user_id)
        resp = requests.post(BASE_URL, headers=h, cookies=self.cookie, data=pkt.SerializeToString())
        resp.raise_for_status()
        return decode_create_chat_response(resp.content)

    def send_message(self, text, chat_id):
        """Send a text message to a chat_id."""
        h = _proto_headers(cmd=5, cmd_version="5.7.0")
        pkt = build_send_message_proto(text, h["x-request-id"], chat_id)
        resp = requests.post(BASE_URL, headers=h, cookies=self.cookie, data=pkt.SerializeToString())
        resp.raise_for_status()
        return resp.status_code == 200

    def send_to_user(self, user_name, text):
        """Search user by name → create chat → send message. Returns chat_id."""
        results = self.search(user_name)
        users = [r for r in results if r["type"] == "user"]
        if not users:
            raise RuntimeError(f"No user found for '{user_name}'")
        user_id = users[0]["id"]
        chat_id = self.create_chat(user_id)
        if not chat_id:
            raise RuntimeError(f"Failed to create chat with user {user_id}")
        self.send_message(text, chat_id)
        return chat_id

    def get_user_name(self, user_id, chat_id):
        """Get a user's display name."""
        h = _proto_headers(cmd=5023)
        pkt = build_get_user_name_proto(h["x-request-id"], user_id, chat_id)
        resp = requests.post(BASE_URL, headers=h, cookies=self.cookie, data=pkt.SerializeToString())
        resp.raise_for_status()
        return decode_user_name_response(resp.content)

    def get_group_name(self, chat_id):
        """Get a group chat's display name."""
        h = _proto_headers(cmd=64)
        pkt = build_get_group_name_proto(h["x-request-id"], chat_id)
        resp = requests.post(BASE_URL, headers=h, cookies=self.cookie, data=pkt.SerializeToString())
        resp.raise_for_status()
        return decode_group_name_response(resp.content)

    def build_ws_url(self):
        """Build WebSocket URL with auth params for message listening."""
        from urllib.parse import urlencode
        h = _common_headers()
        h.update({
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        })
        device_id = self.cookie.get("passport_web_did", "")
        resp = requests.get(MESSENGER_URL, cookies=self.cookie, headers=h)
        app_key = re.findall(r'appKey: "(.*?)"', resp.text)[0]
        access_key = generate_access_key(f"2{app_key}{device_id}f8a69f1719916z")

        resp2 = requests.get(TICKET_URL, headers=h, cookies=self.cookie,
                             params={"local_device_id": device_id})
        ticket = resp2.json().get("ticket")

        params = {
            "access_key": access_key,
            "aid": "1",
            "ticket": ticket,
            "device_id": device_id,
            "fpid": "2",
            "accept_encoding": "gzip",
            "request_id": generate_request_id(),
        }
        return f"{WS_URL}?{urlencode(params)}"
