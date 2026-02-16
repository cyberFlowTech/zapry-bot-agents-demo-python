# Zapry Bot Agents Demo (Python)

A minimal but feature-complete **Echo Bot** demonstrating how to build Zapry Bot Agents using [`zapry-bot-sdk-python`](https://github.com/cyberFlowTech/zapry-bot-sdk-python).

Clone → configure → run in **under 5 minutes**.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/cyberFlowTech/zapry-bot-agents-demo-python.git
cd zapry-bot-agents-demo-python

# 2. Create your environment file
cp .env.example .env
# Edit .env and paste your Telegram bot token (get one from @BotFather)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the bot
python bot.py
```

> **Tip:** For Zapry platform usage, see [Environment Variables](#environment-variables) below.

---

## Project Structure

```
zapry-bot-agents-demo-python/
├── bot.py                  # Entry point — start/help (decorator pattern)
├── handlers/
│   ├── __init__.py
│   └── echo.py             # Echo handlers (manual registration pattern)
├── services/
│   ├── __init__.py
│   └── echo_service.py     # Business logic layer
├── .env.example            # Annotated environment config template
├── requirements.txt        # Python dependencies
└── README.md               # You are here
```

---

## How It Works

```
┌────────────────────┐
│   User Message      │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐      ┌─────────────────────┐
│   ZapryBot (SDK)   │◄─────│  BotConfig.from_env()│
│   - Telegram mode  │      │  (.env configuration) │
│   - Zapry mode     │      └─────────────────────┘
└────────┬───────────┘
         │  routes to matching handler
         ▼
┌────────────────────────────────────────────────┐
│                  Handlers                       │
│                                                 │
│  bot.py (decorators)    handlers/echo.py        │
│  ├── /start             ├── /echo <text>        │
│  ├── /help              ├── echo_again callback │
│  └── about callback     ├── echo_stats callback │
│                         └── free-text message   │
└────────────────┬───────────────────────────────┘
                 │  calls service methods
                 ▼
┌────────────────────────────────────────────────┐
│              Service Layer                      │
│                                                 │
│  services/echo_service.py                       │
│  ├── format_echo(text, user_name)               │
│  ├── get_about_text()                           │
│  └── get_stats()                                │
└────────────────────────────────────────────────┘
```

### Handler Registration — Two Patterns

This demo intentionally uses **both** patterns so you can pick the one that fits:

| Pattern | Where | Best For |
|---------|-------|----------|
| **Decorator** `@bot.command("start")` | `bot.py` | Simple handlers defined in the entry point |
| **Manual** `bot.add_command("echo", handler)` | `handlers/echo.py` → `register(bot)` | Multi-file projects with separated concerns |

---

## SDK API Quick Reference

### Initialisation

```python
from zapry_bot_sdk import BotConfig, ZapryBot

config = BotConfig.from_env()   # reads .env automatically
bot    = ZapryBot(config)
bot.run()                        # blocking — starts polling or webhook
```

### Handler Registration

| Method | Signature | Description |
|--------|-----------|-------------|
| `bot.add_command()` | `(name, handler, **kw)` | Register a `/command` handler |
| `bot.add_callback_query()` | `(pattern, handler, **kw)` | Register callback query handler (regex pattern) |
| `bot.add_message()` | `(filter_obj, handler, **kw)` | Register message handler with Telegram filters |

### Decorators

| Decorator | Description |
|-----------|-------------|
| `@bot.command(name)` | Shortcut for `add_command` |
| `@bot.callback_query(pattern)` | Shortcut for `add_callback_query` |
| `@bot.message(filter_obj)` | Shortcut for `add_message` |
| `@bot.on_error` | Global error handler |
| `@bot.on_post_init` | Lifecycle hook — after init |
| `@bot.on_post_shutdown` | Lifecycle hook — before shutdown |

### Handler Signature

All handlers follow the standard `python-telegram-bot` signature:

```python
async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ...
```

---

## Creating Your Own Bot

Follow these steps to build a new Zapry Bot Agent from scratch:

### Step 1 — Scaffold

```bash
mkdir my-zapry-bot && cd my-zapry-bot
cp /path/to/this-demo/.env.example .env
cp /path/to/this-demo/requirements.txt .
pip install -r requirements.txt
```

### Step 2 — Entry Point (`bot.py`)

```python
from zapry_bot_sdk import BotConfig, ZapryBot
from telegram import Update
from telegram.ext import ContextTypes

config = BotConfig.from_env()
bot = ZapryBot(config)

@bot.command("start")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello from my bot!")

if __name__ == "__main__":
    bot.run()
```

### Step 3 — Add a Handler Module

Create `handlers/greet.py`:

```python
from telegram import Update
from telegram.ext import ContextTypes

async def greet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(f"Hi {name}! 👋")

def register(bot):
    bot.add_command("greet", greet_command)
```

Register it in `bot.py`:

```python
from handlers.greet import register as register_greet
register_greet(bot)
```

### Step 4 — Add a Service

Create `services/greet_service.py`:

```python
class GreetService:
    def format_greeting(self, name: str) -> str:
        return f"🎉 Welcome, {name}! Great to see you."

greet_service = GreetService()
```

Import and use it in your handler:

```python
from services.greet_service import greet_service

async def greet_command(update, context):
    name = update.effective_user.first_name
    await update.message.reply_text(greet_service.format_greeting(name))
```

### Step 5 — Run & Test

```bash
python bot.py
```

Open your bot in Telegram and send `/start` or `/greet`.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TG_PLATFORM` | `telegram` | Platform: `telegram` or `zapry` |
| `TELEGRAM_BOT_TOKEN` | — | Bot token (Telegram platform) |
| `ZAPRY_BOT_TOKEN` | — | Bot token (Zapry platform) |
| `ZAPRY_API_BASE_URL` | `https://openapi.mimo.immo/bot` | Zapry API base URL |
| `RUNTIME_MODE` | `polling` | `polling` (dev) or `webhook` (production) |
| `TELEGRAM_WEBHOOK_URL` | — | Public webhook URL (Telegram) |
| `ZAPRY_WEBHOOK_URL` | — | Public webhook URL (Zapry) |
| `WEBHOOK_PATH` | `""` | Webhook URL path suffix |
| `WEBAPP_HOST` | `0.0.0.0` | Webhook server listen host |
| `WEBAPP_PORT` | `8443` | Webhook server listen port |
| `WEBHOOK_SECRET_TOKEN` | — | Webhook verification secret |
| `DEBUG` | `false` | Enable verbose logging |

---

## Deployment

### Development (Polling)

```env
RUNTIME_MODE=polling
TELEGRAM_BOT_TOKEN=your-token
```

Just run `python bot.py`. No public URL needed.

### Production (Webhook)

```env
RUNTIME_MODE=webhook
TELEGRAM_BOT_TOKEN=your-token
TELEGRAM_WEBHOOK_URL=https://your-domain.com
WEBAPP_PORT=8443
```

Set up a reverse proxy (Nginx / Caddy) to forward HTTPS traffic to the bot's port.

Example Nginx config:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate     /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

### Zapry Platform

```env
TG_PLATFORM=zapry
ZAPRY_BOT_TOKEN=your-zapry-token
ZAPRY_API_BASE_URL=https://openapi.mimo.immo/bot
RUNTIME_MODE=webhook
ZAPRY_WEBHOOK_URL=https://your-domain.com
```

---

## Advanced Example

For a full-featured production bot, see [fortune_master](https://github.com/cyberFlowTech/fortune_master) — a tarot reading bot that demonstrates:

- Multi-step conversation flows
- Tarot card data management and interpretation
- Group chat support
- Session and history management
- Chain monitoring services
- Zapry wallet integration

---

## Links

- [zapry-bot-sdk-python](https://github.com/cyberFlowTech/zapry-bot-sdk-python) — The SDK this demo is built on
- [python-telegram-bot](https://docs.python-telegram-bot.org/) — Underlying Telegram library
- [Zapry Developer Portal](https://zapry.io) — SDK docs and dashboard

---

## License

MIT
