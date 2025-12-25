# MiniMax Agent API Wrapper

A Python wrapper and local API server for the MiniMax Agent platform. This project reverse-engineers the request signing headers (`x-signature`, `yy`) to allow programmatic interaction with the chat interface.

## Features

- **Authentication**: Replicates browser credentials and calculates dynamic signatures.
- **TLS Fingerprinting**: Uses `curl_cffi` to mimic Firefox, bypassing Cloudflare protections.
- **Local API**: Provides a FastAPI server to send messages and poll for responses.
- **Long-running Support**: Handles token reuse and timestamp calculation automatically.

## Prerequisites

- Python 3.8+
- A MiniMax account (logged in via browser)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/JMJAJ/minimax-wrapper.git
   cd minimax-wrapper
   ```

2. Install dependencies:
   ```bash
   pip install curl_cffi fastapi uvicorn python-dotenv
   ```

## Configuration

1. Log in to [MiniMax Agent](https://agent.minimax.io) in your browser.
2. Open Developer Tools (**F12**) and go to the **Console** tab.
3. Paste the contents of `get_credentials.js` into the console.
4. Create a file named `.env` in the project root and paste the output. It should look like this:

   ```env
   MINIMAX_TOKEN=eyJhbGciOiJIUz...
   MINIMAX_USER_ID=460406...
   MINIMAX_DEVICE_ID=448877...
   ```

## Usage

### Start the Server

```bash
python main.py
```

The server will check your credits on startup and listen on `http://127.0.0.1:8000`.

### API Endpoints

#### `POST /chat`

Send a message to the AI.

**Request:**

```json
{
  "message": "Write a python script to parse CSV files.",
  "chat_id": null 
}
```
*Note: Set `chat_id` to continue an existing conversation. Leave `null` to start a new one.*

**Response:**

```json
{
  "response": "Here is the Python script...",
  "chat_id": 348470373945430,
  "thinking": "The user wants a CSV parser. I should use the pandas library..."
}
```

### Example cURLs

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello!"}'
```

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d "{\"message\": \"Tell me a joke.\", \"chat_id\": 348470373945430}"
```

## Reverse Engineering Process

To successfully communicate with the API, I had to replicate the browser's request signing and bypass Cloudflare's bot detection.

### 1. Request Signing (`x-signature` & `yy`)
The API rejects any request that doesn't contain valid `x-signature` and `yy` headers matching the current timestamp. By analyzing the minified JavaScript (specifically chunk `95314`), I extracted the signing algorithm.

**The Signature Logic:**
- **x-signature:** `MD5( timestamp + SECRET_KEY + request_body )`
- **yy:** `MD5( UrlEncodedPath + "_" + request_body + MD5(timestamp) + "ooui" )`

The static secret key found in the source was `I*7Cf%WZ#S&%1RlZJ&C2`.

### 2. TLS Fingerprinting (JA3)
Even with valid signatures, standard Python `requests` caused a `403 Forbidden` error. This was due to Cloudflare analyzing the TLS Client Hello packet (JA3 fingerprinting).

I solved this by using `curl_cffi`, which allows us to impersonate a real browser's TLS fingerprint (Firefox in this case), making the Python script indistinguishable from a legitimate browser session.

## Disclaimer

This project is for educational purposes only. It is not affiliated with MiniMax. Use responsibly and ensure you comply with the platform's Terms of Service.