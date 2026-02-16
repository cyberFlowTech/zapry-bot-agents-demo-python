# Zapry Bot Agents Demo (Python)

A full-featured **AI Agent** template built with [zapry-bot-sdk-python](https://github.com/cyberFlowTech/zapry-bot-sdk-python), demonstrating production-ready patterns for building intelligent bot agents on Telegram and Zapry platforms.

Clone → configure → run in **under 5 minutes**.

---

## What This Demo Covers

| Capability | Module | Description |
|-----------|--------|-------------|
| **AI Conversation** | `services/ai_chat.py` | OpenAI integration with customizable persona |
| **Long-term Memory** | `services/user_memory.py` | Bot remembers user details across sessions |
| **Memory Extraction** | `services/memory_extractor.py` | AI auto-extracts user info from conversations |
| **Intent Recognition** | `services/intent_router.py` | Natural language → command routing via LLM |
| **Tarot Reading** | `services/tarot_data.py` | Multi-step card reveal with interpretations |
| **Group Features** | `handlers/group.py` | Daily fortune, leaderboard, PvP battles |
| **USDT Payments** | `services/payment.py` + `wallet.py` | HD wallet per user, BSC chain monitoring, auto-sweep |
| **Quota System** | `services/quota.py` | Daily free limits + pay-per-use |
| **Data Persistence** | `db/database.py` | SQLite with WAL mode, async operations |
| **Platform Compat** | SDK built-in | Zapry API differences handled automatically |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/cyberFlowTech/zapry-bot-agents-demo-python.git
cd zapry-bot-agents-demo-python

# 2. Configure
cp .env.example .env
# Edit .env: add your bot token and OpenAI API key

# 3. Install
pip install -r requirements.txt

# 4. Run
python bot.py
```

> For Zapry platform, set `TG_PLATFORM=zapry` in `.env`. See [Environment Variables](#environment-variables).

---

## Project Structure

```
zapry-bot-agents-demo-python/
├── bot.py                       # Entry point — SDK init, /start, /help, lifecycle hooks
├── config.py                    # Environment config loader
│
├── handlers/                    # User-facing command & message handlers
│   ├── chat.py                  # AI chat + intent routing + memory commands
│   ├── tarot.py                 # Tarot reading (progressive card reveal)
│   ├── fortune.py               # Quick fortune guidance
│   ├── luck.py                  # Daily energy score
│   ├── group.py                 # Group fortune / leaderboard / PvP
│   └── payment.py               # Recharge / balance / admin top-up
│
├── services/                    # Business logic layer
│   ├── ai_chat.py               # OpenAI client + persona prompt loading
│   ├── intent_router.py         # NLU: natural language → command intent
│   ├── user_memory.py           # Long-term user profile (SQLite + cache)
│   ├── memory_extractor.py      # AI extracts user info from chat history
│   ├── chat_history.py          # Conversation history persistence
│   ├── conversation_buffer.py   # Buffer for memory extraction triggers
│   ├── tarot_data.py            # 22 Major Arcana cards + interpretation
│   ├── tarot_history.py         # Reading history persistence
│   ├── group_manager.py         # Group data (fortune, ranking, PK)
│   ├── quota.py                 # Daily free quota + balance deduction
│   ├── payment.py               # Balance management + recharge orders
│   ├── wallet.py                # HD wallet (BIP-44) + sweep signing
│   └── chain_monitor.py         # BSC RPC polling + auto-sweep
│
├── db/
│   └── database.py              # SQLite manager (WAL, async, auto-init)
│
├── prompts/
│   ├── elena_character.txt      # Full persona (default: tarot reader)
│   └── agent_character.txt      # Minimal persona template for customization
│
├── utils/
│   └── zapry_compat.py          # Markdown cleaning utility
│
├── .env.example                 # Annotated configuration template
├── requirements.txt             # Python dependencies
└── README.md
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Message                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  ZapryBot (SDK)                               │
│  • Telegram / Zapry auto-compat                              │
│  • Handler routing                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ Intent Router│ │ Command  │ │  Callback    │
│ (LLM-based) │ │ Handlers │ │  Handlers    │
└──────┬───────┘ └────┬─────┘ └──────┬───────┘
       │              │              │
       └──────────────┼──────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                               │
│                                                               │
│  ai_chat ←→ user_memory ←→ memory_extractor                  │
│  tarot_data ←→ tarot_history                                  │
│  payment ←→ wallet ←→ chain_monitor                           │
│  quota (checks free limits + balance)                         │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              SQLite Database (WAL mode)                       │
│                                                               │
│  user_memories │ chat_history │ tarot_readings │ daily_usage  │
│  user_balances │ user_wallets │ recharge_orders│ spend_records│
│  group_fortunes│ group_rankings│ pk_records    │ conv_buffer  │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### 1. AI Persona (`prompts/`)

The bot's personality is defined in a text file loaded by `services/ai_chat.py`. Two files are included:

- **`elena_character.txt`** — Full persona: a 28-year-old tarot reader named Elena. ~500 lines covering personality, background, speaking style, emotional responses, and strict identity boundaries.
- **`agent_character.txt`** — Minimal template for building your own persona.

**To customize:** Edit or replace the prompt file. No code changes needed.

### 2. Long-term Memory

The bot remembers what users tell it across sessions:

```
User: "I'm 25, working as a designer in Beijing"
  → memory_extractor (AI) extracts: age=25, occupation=designer, location=Beijing
  → user_memory stores to SQLite
  → Next conversation: AI naturally references these details
```

### 3. Intent Recognition

Users can talk naturally instead of using commands:

```
"帮我看看事业运" → detected as /tarot intent → routes to tarot handler
"还剩多少余额"   → detected as /balance intent → routes to payment handler
"你是谁"         → detected as /intro intent → routes to intro handler
```

Three-tier detection: fast keyword matching → chat shortcuts → LLM fallback.

### 4. USDT Payment System

Each user gets a unique BSC deposit address (derived via HD wallet BIP-44):

```
User → /recharge → sees their unique BSC address
User → transfers USDT on-chain
Bot  → detects via BSC RPC polling → confirms deposit → adds balance
Bot  → auto-sweeps USDT to cold wallet
```

No shared address, no amount matching, zero collision risk.

---

## Handler Registration — SDK Pattern

Each handler module exports a `register(bot)` function:

```python
# handlers/fortune.py

async def fortune_command(update, context):
    ...

def register(bot):
    bot.add_command("fortune", fortune_command)
```

Registered in `bot.py`:

```python
from handlers.fortune import register as reg_fortune
reg_fortune(bot)
```

### SDK API Reference

| Method | Signature | Description |
|--------|-----------|-------------|
| `bot.add_command()` | `(name, handler)` | Register `/command` handler |
| `bot.add_callback_query()` | `(pattern, handler)` | Register callback query (regex) |
| `bot.add_message()` | `(filter, handler, group=N)` | Register message handler |
| `@bot.command(name)` | decorator | Shortcut for `add_command` |
| `@bot.on_post_init` | decorator | Lifecycle: after init |
| `@bot.on_post_shutdown` | decorator | Lifecycle: before shutdown |
| `@bot.on_error` | decorator | Global error handler |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TG_PLATFORM` | `telegram` | Platform: `telegram` or `zapry` |
| `TELEGRAM_BOT_TOKEN` | — | Bot token (Telegram) |
| `ZAPRY_BOT_TOKEN` | — | Bot token (Zapry) |
| `ZAPRY_API_BASE_URL` | `https://openapi.mimo.immo/bot` | Zapry API endpoint |
| `RUNTIME_MODE` | `polling` | `polling` (dev) or `webhook` (prod) |
| `OPENAI_API_KEY` | — | OpenAI API key (required for AI features) |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM model |
| `BSC_WALLET_ADDRESS` | — | Cold wallet for USDT sweep |
| `HD_MNEMONIC` | — | HD wallet seed (BIP-39, 12 words) |
| `FREE_TAROT_DAILY` | `1` | Free tarot readings per day |
| `FREE_CHAT_DAILY` | `10` | Free AI chats per day |
| `DEBUG` | `false` | Verbose logging |

See `.env.example` for the complete list with annotations.

---

## Deployment

### Development (Polling)

```env
RUNTIME_MODE=polling
TELEGRAM_BOT_TOKEN=your-token
OPENAI_API_KEY=your-key
```

Just run `python bot.py`.

### Production (Webhook)

```env
RUNTIME_MODE=webhook
TELEGRAM_BOT_TOKEN=your-token
TELEGRAM_WEBHOOK_URL=https://your-domain.com
WEBAPP_PORT=8443
```

### Zapry Platform

```env
TG_PLATFORM=zapry
ZAPRY_BOT_TOKEN=your-zapry-token
RUNTIME_MODE=webhook
ZAPRY_WEBHOOK_URL=https://your-domain.com
```

---

## Customization Guide

### Replace the AI Persona

1. Edit `prompts/agent_character.txt` (or create a new file)
2. Update `services/ai_chat.py` to load your file
3. Update user-facing text in `handlers/` to match the new persona

### Add a New Skill

1. Create `services/my_skill.py` with business logic
2. Create `handlers/my_skill.py` with command handler + `register(bot)` function
3. Import and call `register()` in `bot.py`

### Disable Payment Features

Remove or comment out in `bot.py`:

```python
# from handlers.payment import register as reg_payment
# reg_payment(bot)
```

And remove the chain monitor from `post_init`.

---

## Advanced Reference

For the original production bot that this demo is based on, see [fortune_master](https://github.com/cyberFlowTech/zapry-bot-tarotmaster) — a fully deployed tarot reading bot with:

- Complete Lin Wanqing (Elena) persona (~500 lines)
- Zapry API compatibility layer (14 known differences documented)
- Performance optimizations (async pipelines, SQLite PRAGMA tuning)
- Battle-tested with real users on Zapry platform

---

## Links

- [zapry-bot-sdk-python](https://github.com/cyberFlowTech/zapry-bot-sdk-python) — The SDK this demo is built on
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) — Underlying Telegram library
- [Zapry Developer Portal](https://mimo.immo) — SDK docs and dashboard

---

## License

MIT
