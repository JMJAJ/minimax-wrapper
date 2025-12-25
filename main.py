import time
import json
import hashlib
import urllib.parse
import asyncio
import os
from contextlib import asynccontextmanager
from typing import Optional

from curl_cffi import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

MINIMAX_TOKEN = os.getenv("MINIMAX_TOKEN")
MINIMAX_USER_ID = os.getenv("MINIMAX_USER_ID")
MINIMAX_DEVICE_ID = os.getenv("MINIMAX_DEVICE_ID")

if not all([MINIMAX_TOKEN, MINIMAX_USER_ID, MINIMAX_DEVICE_ID]):
    raise ValueError("Missing credentials in .env file. Run get_credentials.js in browser console.")

class MiniMaxClient:
    def __init__(self, token, user_id, device_id):
        self.base_url = "https://agent.minimax.io"
        self.token = token
        self.user_id = user_id
        self.device_id = device_id
        self.session = requests.Session()
        
        self.base_headers = {
            "Host": "agent.minimax.io",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "token": self.token,
            "Origin": "https://agent.minimax.io",
            "Referer": "https://agent.minimax.io/",
            "Cookie": (
                "locale_preference=en; "
                f"_token={self.token}; "
                f"sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22R7wPGAXQpAlY%22%2C%22first_id%22%3A%2219b5315bbdb5b4-07b3841bcff5e3-8535026-2559600-19b5315bbdc1249%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E8%87%AA%E7%84%B6%E6%90%9C%E7%B4%A2%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fwww.google.com%2F%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTliNTMxNWJiZGI1YjQtMDdiMzg0MWJjZmY1ZTMtODUzNTAyNi0yNTU5NjAwLTE5YjUzMTViYmRjMTI0OSIsIiRpZGVudGl0eV9sb2dpbl9pZCI6IlI3d1BHQVhRcEFsWSJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%22R7wPGAXQpAlY%22%7D%2C%22%24device_id%22%3A%22{self.device_id}%22%7D"
            )
        }

    def _calculate_md5(self, data: str) -> str:
        return hashlib.md5(data.encode('utf-8')).hexdigest()

    def _get_security_headers(self, endpoint, params, payload):
        ts = str(int(time.time()))
        body_str = json.dumps(payload, separators=(',', ':')) if payload else "{}"
        
        # Static salt reversed from JS bundle
        secret_key = "I*7Cf%WZ#S&%1RlZJ&C2"
        x_signature = self._calculate_md5(f"{ts}{secret_key}{body_str}")
        
        query_string = urllib.parse.urlencode(params)
        full_path_with_query = f"{endpoint}?{query_string}"
        encoded_path = urllib.parse.quote(full_path_with_query, safe='')
        
        yy_payload = f"{encoded_path}_{body_str}{self._calculate_md5(ts)}ooui"
        yy = self._calculate_md5(yy_payload)
        
        return {"x-timestamp": ts, "x-signature": x_signature, "yy": yy}

    def post(self, endpoint, payload=None):
        if payload is None: payload = {}
        
        params = {
            "device_platform": "web",
            "biz_id": "3",
            "app_id": "3001",
            "version_code": "22201",
            "unix": str(int(time.time() * 1000)),
            "timezone_offset": "3600",
            "lang": "en",
            "uuid": "5bd9d6fe-4e94-419f-925c-b0a72b010c56",
            "device_id": self.device_id,
            "os_name": "Windows",
            "browser_name": "firefox",
            "cpu_core_num": "12",
            "browser_language": "en-US",
            "browser_platform": "Win32",
            "user_id": self.user_id,
            "screen_width": "2133",
            "screen_height": "1200",
            "token": self.token
        }

        security_headers = self._get_security_headers(endpoint, params, payload)
        headers = {**self.base_headers, **security_headers}
        url = f"{self.base_url}{endpoint}"
        
        response = self.session.post(url, headers=headers, params=params, json=payload, impersonate="firefox")
        
        if response.status_code != 200:
            print(f"[!] Request to {endpoint} failed: {response.status_code}")
            raise Exception(f"API Error {response.status_code}")
            
        return response.json()

    def get_membership_info(self):
        return self.post("/matrix/api/v1/commerce/get_membership_info")

    def send_chat_message(self, text, chat_id=None):
        payload = {
            "msg_type": 1,
            "text": text,
            "chat_type": 1,
            "attachments": [],
            "selected_mcp_tools": [],
            "sub_agent_ids": [],
            "model_option": {"display_name": "MiniMax-M2.1", "model_type": 0}
        }
        if chat_id: payload["chat_id"] = chat_id
        return self.post("/matrix/api/v1/chat/send_msg", payload)

    def get_chat_detail(self, chat_id):
        return self.post("/matrix/api/v1/chat/get_chat_detail", {"chat_id": chat_id})

# --- Server Logic ---

client = MiniMaxClient(MINIMAX_TOKEN, MINIMAX_USER_ID, MINIMAX_DEVICE_ID)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*40)
    print("[*] Connecting to MiniMax...")
    try:
        info = client.get_membership_info()
        print(f"[+] Connected as: {info.get('plan_name')}")
        print(f"[+] Credits:      {info.get('total_remains_credit')}")
    except Exception as e:
        print(f"[!] Connection failed: {e}")
    print("="*40 + "\n")
    yield

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[int] = None

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        print(f"[*] Sending message: '{req.message}' (Chat ID: {req.chat_id})")
        send_resp = client.send_chat_message(req.message, req.chat_id)
        
        chat_id = send_resp.get("chat_id")
        user_msg_id = send_resp.get("msg_id")
        
        if not chat_id:
            raise HTTPException(status_code=500, detail="Failed to create/send to chat")

        print(f"[*] Polling for response in Chat ID {chat_id}...")
        for _ in range(45): # Timeout ~90s
            await asyncio.sleep(2)
            details = client.get_chat_detail(chat_id)
            messages = details.get("messages", [])
            messages.sort(key=lambda x: x['timestamp'])
            
            if not messages: continue

            last_msg = messages[-1]
            # Check if latest message is from AI (type 2) and distinct from user prompt
            if last_msg.get('msg_type') == 2 and last_msg.get('msg_id') != user_msg_id:
                if last_msg.get('msg_content'):
                    return {
                        "response": last_msg.get('msg_content'),
                        "chat_id": chat_id,
                        "thinking": last_msg.get('extra_info', {}).get('thinking_content')
                    }
        
        raise HTTPException(status_code=408, detail="Timeout waiting for AI response")

    except Exception as e:
        print(f"[!] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)