# Mochi — Discord AI Companion Bot

Mochi is a Discord bot powered by Google's Gemini API. It chats with users who
@mention it, remembers recent conversation per user, and can switch between
several personalities with a slash command.

## Features

- **Multiple personalities** — switch Mochi's personality with `/persona`:
  - 🤖 Default (No Persona)
  - ☕ Cozy Café Girl
  - 🐈 Sleepy Cat Café
  - 🌙 Study Buddy
  - 💪 Motivational Coach
  - 👵 Loving Lola
  - 🧑‍🏫 Patient Tutor
  - 🗣️ Multilingual Language Buddy
  - 😏 Sarcastic Bestie
  - 🌧️ Rainy Day Listener
- **Per-user memory** — each person gets their own conversation history and
  persona choice, independent of everyone else in the server.
- **Sliding-window memory** — conversation history resets automatically after
  a set number of turns, to keep replies fast and affordable. Say `reset` to
  clear your own history early.
- **Safety limits** — a per-user cooldown, a prompt length cap, a response
  timeout, and a global token-budget guard so the bot degrades gracefully
  under heavy use instead of erroring out.
- **Multilingual** — understands and can reply in English, Tagalog, and
  Bisaya.

## Tech stack

- [discord.py](https://discordpy.readthedocs.io/) for the Discord bot
- [google-genai](https://pypi.org/project/google-genai/) for the Gemini API
  (currently using `gemini-3.5-flash-lite`)
- [staypresent](https://pypi.org/project/staypresent/) to keep the bot alive
  on Render's free web-service tier

## Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd <your-repo-folder>
pip install -r requirements.txt
```

### 2. Get your keys

- **Discord bot token** — create an application at the
  [Discord Developer Portal](https://discord.com/developers/applications),
  add a Bot user, and copy its token. Under **OAuth2 → URL Generator**, check
  the `bot` and `applications.commands` scopes to generate an invite link.
  Under **Bot**, enable the **Message Content** privileged intent.
- **Gemini API key** — get one from
  [Google AI Studio](https://ai.google.dev/gemini-api/docs/api-key).

### 3. Set environment variables

```bash
export DISCORD_TOKEN="your_discord_bot_token"
export GEMINI_API_KEY="your_gemini_api_key"
```

On Render (or another host), set these in the service's **Environment**
settings instead.

### 4. Run it

Locally, for quick testing:

```bash
python bot.py
```

For deployment (e.g. Render), the entry point is `main.py`, which wraps
`bot.py` with `staypresent` so the service stays alive on a free web-service
plan:

```bash
python main.py
```

## Usage

- **Chat:** @mention the bot with your message.
- **Switch personality:** run `/persona` and pick from the dropdown.
- **Reset your memory:** @mention the bot and say `reset`.

## Configuration

A few constants near the top of `bot.py` are worth knowing about if you want
to tune behavior:

| Constant | Purpose |
|---|---|
| `MODEL_NAME` | Which Gemini model to use |
| `MAX_TURNS` | How many turns before a user's history resets |
| `COOLDOWN_SECONDS` | Minimum seconds between messages per user |
| `MAX_PROMPT_CHARS` | Max characters read from a single message |
| `API_TIMEOUT_SECONDS` | How long to wait for Gemini before giving up |
| `TPM_LIMIT` | Your Gemini tier's tokens-per-minute quota |

## Notes

- Conversation history and persona choices are kept in memory only — they
  reset whenever the bot restarts or redeploys.
- The bot is not a substitute for professional support. The Rainy Day
  Listener persona includes guidance to point people toward real help if
  they mention serious distress.

## License

Add a license of your choice here (MIT is a common, permissive default for
personal projects).
