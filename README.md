# MiniMax Agent API Wrapper

A robust Python wrapper and local API server for the MiniMax Agent platform. This project reverse-engineers the request signing headers (`x-signature`, `yy`) to allow programmatic interaction with the chat interface. It supports both **Lightning** and **Pro** models and works seamlessly with the **Free Tier**.

<img width="678" height="236" alt="MiniMax CLI Screenshot" src="https://github.com/user-attachments/assets/f2a60b9e-8d8a-4cde-b552-98a2650c51f9" />

## Features

- **Authentication**: Replicates browser credentials and calculates dynamic request signatures in real-time.
- **TLS Fingerprinting**: Utilizes `curl_cffi` to mimic Firefox, successfully bypassing Cloudflare bot detection.
- **Interactive CLI**: 
  - Full terminal-based chat interface.
  - Supports model selection (**Lightning** vs **Pro**).
  - Context-aware history loading for resuming conversations.
  - Visualized "Thinking Process" bubbles.
- **Local API Server**: Exposes a FastAPI endpoint to integrate MiniMax into other applications.
- **Auto-Recovery**: Automatically handles token reuse, session refreshing, and polling timeouts.

## Prerequisites

- Python 3.8+
- A valid MiniMax account (logged in via browser)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/JMJAJ/minimax-wrapper.git
   cd minimax-wrapper
   ```

2. Install the required dependencies:
   ```bash
   pip install curl_cffi fastapi uvicorn python-dotenv prompt_toolkit rich
   ```

## Configuration

1. Log in to [MiniMax Agent](https://agent.minimax.io) in your web browser.
2. Open Developer Tools (**F12**) and navigate to the **Console** tab.
3. Paste the contents of the `get_credentials.js` file (included in this repo) into the console and hit Enter.
4. Copy the output and create a file named `.env` in the project root directory:

   ```env
   MINIMAX_TOKEN=eyJhbGciOiJIUz...
   MINIMAX_USER_ID=460406...
   MINIMAX_DEVICE_ID=448877...
   ```

## Usage

Start the main script:
```bash
python main.py
```

You will be presented with two modes:

1. **Interactive CLI Chat**: A terminal chat experience. Select `0` to start a new chat (prompting for model selection), or select an existing Chat ID to resume history.
2. **API Server**: Starts a local REST API on port `8000`.

---

## API Documentation

When running in **Server Mode**, the application listens on `http://127.0.0.1:8000`.

### Endpoint: `POST /chat`

Sends a message to the AI and waits for the complete response.

**Request Body:**

```json
{
  "message": "Write a python script to parse CSV files.",
  "chat_id": null,
  "use_pro": false
}
```
*   **chat_id**: Set to `null` to start a new conversation, or provide an integer ID to continue one.
*   **use_pro**: Set to `true` to use the Pro (Agent) model, or `false` for Lightning.

**Response:**

```json
{
  "response": "Here is the Python script...",
  "chat_id": 348470373945430,
  "thinking": "The user wants a CSV parser. I should use the pandas library..."
}
```

### Client Examples

#### cURL (Linux / macOS / Git Bash)

**Start a New Chat (Lightning):**
```bash
curl -X POST "http://127.0.0.1:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello, explain quantum physics briefly."}'
```

**Start a New Chat (Pro Mode):**
```bash
curl -X POST "http://127.0.0.1:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Write a detailed research report on AI.", "use_pro": true}'
```

**Continue a Chat:**
```bash
curl -X POST "http://127.0.0.1:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Tell me more about the second point.", "chat_id": 3484703739...}'
```

#### PowerShell (Windows)

**Option A: Structured Request**
```powershell
$params = @{
    Uri         = "http://127.0.0.1:8000/chat"
    Method      = "Post"
    ContentType = "application/json"
    Body        = @{
        message = "Write a python script to parse CSV files."
        use_pro = $false 
    } | ConvertTo-Json
}

Invoke-RestMethod @params
```

**Option B: Quick One-Liner**
```powershell
irm http://127.0.0.1:8000/chat -Method Post -ContentType 'application/json' -Body '{"message": "Hello!"}'
```

---

## Technical Details: Reverse Engineering

To successfully communicate with the API, this project replicates the browser's request signing process and bypasses Cloudflare's bot detection.

### 1. Request Signing (`x-signature` & `yy`)
The API validates requests using headers generated from the request body and timestamp. By analyzing the minified JavaScript source, we extracted the specific algorithms:

*   **x-signature**: `MD5( timestamp + SECRET_KEY + request_body )`
*   **yy**: `MD5( UrlEncodedPath + "_" + request_body + MD5(timestamp) + "ooui" )`

*The static secret key identified during analysis is `I*7Cf%WZ#S&%1RlZJ&C2`.*

### 2. TLS Fingerprinting (JA3)
Standard Python `requests` libraries trigger Cloudflare's 403 Forbidden errors due to recognizable TLS fingerprints (JA3). This project uses **`curl_cffi`** to impersonate a real Firefox browser's TLS handshake, rendering the script indistinguishable from legitimate user traffic.

## Disclaimer

This project is for educational purposes only. It is not affiliated with, endorsed by, or connected to MiniMax. Use responsibly and ensure you comply with the platform's Terms of Service.