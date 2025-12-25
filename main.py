import time
import json
import hashlib
import urllib.parse
import asyncio
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional, Tuple
from datetime import datetime

from curl_cffi import requests
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from rich.spinner import Spinner
from rich.live import Live

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.patch_stdout import patch_stdout

load_dotenv()

MINIMAX_TOKEN = os.getenv("MINIMAX_TOKEN")
MINIMAX_USER_ID = os.getenv("MINIMAX_USER_ID")
MINIMAX_DEVICE_ID = os.getenv("MINIMAX_DEVICE_ID")

if not all([MINIMAX_TOKEN, MINIMAX_USER_ID, MINIMAX_DEVICE_ID]):
    print("[ERROR] Missing credentials in .env file.")
    sys.exit(1)

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

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
        secret_key = "I*7Cf%WZ#S&%1RlZJ&C2"
        x_signature = self._calculate_md5(f"{ts}{secret_key}{body_str}")
        
        query_string = urllib.parse.urlencode(params)
        full_path_with_query = f"{endpoint}?{query_string}"
        encoded_path = urllib.parse.quote(full_path_with_query, safe='')
        yy = self._calculate_md5(f"{encoded_path}_{body_str}{self._calculate_md5(ts)}ooui")
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
            raise Exception(f"API Error {response.status_code}")
            
        return response.json()

    def get_membership_info(self):
        return self.post("/matrix/api/v1/commerce/get_membership_info")

    def list_chats(self):
        return self.post("/matrix/api/v1/chat/list_chat", {"page_size": 20})

    def delete_chat(self, chat_id):
        return self.post("/matrix/api/v1/chat/delete_chat", {"chat_id": chat_id})

    def send_chat_message(self, text, chat_id=None, use_pro_model=False):
        chat_type = 0 if use_pro_model else 1
        payload = {
            "msg_type": 1,
            "text": text,
            "chat_type": chat_type,
            "attachments": [],
            "selected_mcp_tools": [],
            "sub_agent_ids": [],
            "model_option": {"display_name": "MiniMax-M2.1", "model_type": 0}
        }
        if chat_id: payload["chat_id"] = chat_id
        return self.post("/matrix/api/v1/chat/send_msg", payload)

    def get_chat_detail(self, chat_id):
        return self.post("/matrix/api/v1/chat/get_chat_detail", {"chat_id": chat_id})

client = MiniMaxClient(MINIMAX_TOKEN, MINIMAX_USER_ID, MINIMAX_DEVICE_ID)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*40)
    print("[INFO] Server Mode Started")
    print("="*40 + "\n")
    yield

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[int] = None
    use_pro: Optional[bool] = False

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    final_response = {}
    async for event in chat_logic_generator(req.message, req.chat_id, req.use_pro):
        if event['type'] == 'message':
            final_response['response'] = event.get('content')
            final_response['thinking'] = event.get('thinking')
            final_response['chat_id'] = event.get('chat_id')
        elif event['type'] == 'complete':
            final_response['status'] = 'complete'
            if 'chat_id' not in final_response:
                final_response['chat_id'] = event.get('chat_id')
    return final_response

async def chat_logic_generator(message, chat_id=None, use_pro=False):
    send_resp = client.send_chat_message(message, chat_id, use_pro)
    current_chat_id = send_resp.get("chat_id")
    user_msg_id = send_resp.get("msg_id")

    if not current_chat_id:
        raise Exception("Failed to create chat")

    seen_msg_ids = {user_msg_id}
    max_retries = 120 if use_pro else 60 

    for _ in range(max_retries):
        await asyncio.sleep(2)
        details = client.get_chat_detail(current_chat_id)
        
        server_status = details.get('chat', {}).get('chat_status', 1)
        messages = details.get("messages", [])
        messages.sort(key=lambda x: x['timestamp'])
        
        user_msg_index = -1
        for i, msg in enumerate(messages):
            if msg.get('msg_id') == user_msg_id:
                user_msg_index = i
                break
        
        if user_msg_index == -1:
            continue
            
        new_messages = messages[user_msg_index + 1:]
        has_new_activity = False
        
        for msg in new_messages:
            msg_id = msg.get('msg_id')
            if msg_id in seen_msg_ids:
                continue
                
            seen_msg_ids.add(msg_id)
            has_new_activity = True
            
            if msg.get('msg_type') == 2:
                tool_call = msg.get('tool_call')
                if tool_call:
                    yield {
                        'type': 'tool',
                        'name': tool_call.get('tool_call_name', 'tool') or 'Web Search',
                        'chat_id': current_chat_id
                    }
                    continue

                thinking = msg.get('extra_info', {}).get('thinking_content')
                content = msg.get('msg_content', '')

                if content:
                    yield {
                        'type': 'message',
                        'content': content,
                        'thinking': thinking,
                        'chat_id': current_chat_id
                    }
                elif thinking:
                    yield {
                        'type': 'thinking',
                        'content': thinking,
                        'chat_id': current_chat_id
                    }

        if server_status == 2 and not has_new_activity:
            yield {'type': 'complete', 'chat_id': current_chat_id}
            break
            
        if not use_pro and has_new_activity:
            yield {'type': 'complete', 'chat_id': current_chat_id}
            break

def select_chat_mode() -> Tuple[Optional[int], bool]:
    while True:
        clear_screen()
        console.print(Panel("[bold cyan]MiniMax Agent[/bold cyan]", box=box.SIMPLE))
        
        try:
            with console.status("[dim]Fetching chat history...[/dim]"):
                history = client.list_chats()
                chats = history.get('chats', [])
        except Exception as e:
            console.print(f"[red]Failed to load history:[/red] {e}")
            return None, False

        table = Table(box=box.SIMPLE_HEAD, show_header=True)
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Title", style="white")
        table.add_column("Date", style="dim")
        table.add_row("0", "[bold green]Start New Chat[/bold green]", "-")
        
        chat_map = {}
        for idx, chat in enumerate(chats[:10], 1):
            ts = int(chat.get('create_timestamp', 0)) / 1000
            date_str = datetime.fromtimestamp(ts).strftime('%m-%d %H:%M')
            ctype = "[Pro]" if chat.get('chat_type') == 0 else "[Lightning]"
            title = f"{ctype} {chat.get('chat_title', 'Untitled')}"
            table.add_row(str(idx), title, date_str)
            chat_map[str(idx)] = chat.get('chat_id')

        console.print(table)
        console.print("\n[dim]Select ID, '0' for new, or 'del <ID>' to delete[/dim]")
        
        selection = input("Select > ").strip()
        
        # Deletion Logic
        if selection.lower().startswith("del"):
            parts = selection.split()
            if len(parts) > 1 and parts[1] in chat_map:
                chat_id_to_del = chat_map[parts[1]]
                try:
                    client.delete_chat(chat_id_to_del)
                    console.print(f"[green]Chat {parts[1]} deleted.[/green]")
                    time.sleep(1) 
                    continue # Reload list
                except Exception as e:
                    console.print(f"[red]Failed to delete:[/red] {e}")
                    time.sleep(2)
                    continue
            else:
                console.print("[red]Invalid delete command. Use 'del <ID>'[/red]")
                time.sleep(1)
                continue

        if selection == "0":
            console.print("\n[bold]Select Model:[/bold]")
            console.print("1. [cyan]Lightning[/cyan] (Fast)")
            console.print("2. [magenta]Pro[/magenta] (Smart/Agent)")
            model_sel = input("Model > ").strip()
            return None, (model_sel == "2")

        if selection in chat_map:
            return chat_map[selection], False 
            
        console.print("[red]Invalid selection.[/red]")
        time.sleep(0.5)

async def load_and_display_context(chat_id):
    if not chat_id:
        console.print(f"[dim]Starting New Session[/dim]\n")
        return

    try:
        with console.status("[dim]Loading context...[/dim]"):
            details = client.get_chat_detail(chat_id)
            messages = details.get("messages", [])
            messages.sort(key=lambda x: x['timestamp'])

        if not messages: return
            
        console.print(Panel(f"[bold]History (Last 2 Messages)[/bold]", style="dim", box=box.MINIMAL))
        for msg in messages[-2:]:
            role = "You" if msg.get('msg_type') == 1 else "MiniMax"
            content = msg.get('msg_content', '').strip()
            if role == "You":
                console.print(f"[bold green]You:[/bold green] {content}")
            else:
                preview = content[:300] + "..." if len(content) > 300 else content
                console.print(f"[bold cyan]MiniMax:[/bold cyan] {preview}")
            console.print("")
        console.print("[dim]" + "-"*30 + "[/dim]\n")

    except Exception as e:
        console.print(f"[red]Failed to load context:[/red] {e}")

async def get_input_async(session, text="You > "):
    return await session.prompt_async(HTML(f"<b><style color='green'>{text}</style></b>"))

async def run_cli_mode():
    clear_screen()
    try:
        with console.status("[dim]Initializing...[/dim]"):
            info = client.get_membership_info()
            plan = info.get('plan_name', 'Free')
            credits = info.get('total_remains_credit', 0)
    except Exception as e:
        console.print(f"[red]Connection failed:[/red] {e}")
        return

    current_chat_id, use_pro = select_chat_mode()
    clear_screen()
    model_name = "Pro" if use_pro else "Lightning/Existing"
    
    console.print(Panel(f"[bold]Session Started[/bold]\nPlan: {plan} | Credits: {credits} | Mode: {model_name}\n[dim]Enter to send | Alt+Enter for new line[/dim]\n[dim]To exit, type 'exit' or Ctrl+C[/dim]", box=box.ROUNDED))
    
    await load_and_display_context(current_chat_id)

    kb = KeyBindings()

    @kb.add('enter')
    def _(event):
        event.current_buffer.validate_and_handle()

    @kb.add('escape', 'enter')
    def _(event):
        event.current_buffer.insert_text('\n')

    session = PromptSession(key_bindings=kb, multiline=True)

    while True:
        try:
            with patch_stdout():
                user_input = await get_input_async(session)

            if not user_input.strip(): continue
            if user_input.strip().lower() in ['exit', 'quit']: break
            
            start_time = time.time()
            last_printed_content = ""
            
            with Live(Spinner("dots", text="Sending...", style="cyan"), refresh_per_second=4, console=console) as live:
                async for event in chat_logic_generator(user_input, current_chat_id, use_pro):
                    if event['type'] == 'tool':
                        live.update(Spinner("dots", text=f"Using tool: {event['name']}...", style="yellow"))
                    elif event['type'] == 'thinking':
                        live.update(Spinner("dots", text="Thinking...", style="magenta"))
                    elif event['type'] == 'message':
                        content = event['content']
                        thinking = event.get('thinking')

                        if content and content != last_printed_content:
                            if thinking:
                                live.console.print(Panel(Markdown(thinking), title="[bold]Thinking Process[/bold]", style="dim", box=box.ROUNDED, border_style="yellow"))
                            
                            live.console.print(Panel(Markdown(content), border_style="blue", title="MiniMax", box=box.ROUNDED))
                            last_printed_content = content
                            live.update(Spinner("dots", text="Processing...", style="cyan"))
                        current_chat_id = event['chat_id']
                    elif event['type'] == 'complete':
                        current_chat_id = event['chat_id']
                        live.update(Text("Done.", style="green"))

            end_time = time.time()
            try:
                new_credits = client.get_membership_info().get('total_remains_credit', '?')
            except: new_credits = "?"
                
            console.print(Text(f"Time: {end_time - start_time:.2f}s  |  Credits: {new_credits}", style="grey50"), justify="right")
            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting chat session...[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

if __name__ == "__main__":
    while True:
        clear_screen()
        console.print(Panel("[bold]MiniMax Agent Wrapper[/bold]", box=box.DOUBLE))
        print("1. Interactive CLI Chat")
        print("2. API Server")
        print("3. Exit\n")
        
        choice = input("Enter choice: ").strip()
        if choice == "1":
            try: asyncio.run(run_cli_mode())
            except KeyboardInterrupt: pass
        elif choice == "2":
            clear_screen()
            uvicorn.run(app, host="127.0.0.1", port=8000)
            break
        elif choice == "3":
            sys.exit(0)