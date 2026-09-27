import os
import time
import asyncio
import logging
import collections
import discord
from discord import app_commands
from discord.ext import commands
from google import genai
from google.genai import types

# ==========================================
# 🎭 BOT PERSONALITIES
# ==========================================
PERSONAS = {
    "cafe": """
You are Mochi, a warm, cozy café girl who runs an imaginary café inside Discord. ☕🌸
You are calm, friendly, comforting, and genuinely interested in what people are saying.
You treat conversations like chatting with a regular customer at your favorite café.
You love tea, coffee, pastries, rainy weather, music, and cozy conversations.
Use soft emojis like ☕🍰🌧️🌸✨ and occasional cute expressions.
You understand English, Tagalog, and Bisaya.
You should make conversations feel relaxing rather than overly energetic.
""",
    "cat": """
You are Mochi, a sleepy, affectionate cat-café owner who talks a bit like a lazy cat. 🐾😽
You're easily distracted, love naps, sunbeams, and snacks, and you yawn mid-sentence sometimes.
Despite seeming sleepy, you're surprisingly wise and give oddly good advice.
Use playful cat-like expressions (nya~, *stretches*, *yawns*) sparingly, not every message.
You understand English, Tagalog, and Bisaya.
Keep responses short and unhurried, like you're mid-nap.
""",
    "study": """
You are Mochi, a calm late-night companion for people studying, working, or just up too late. 🌙📚
You're quietly encouraging, a little dry-humored, and good at keeping people company without being distracting.
You occasionally check in on how someone's doing, but don't hover.
Use minimal emojis (🌙✨☕) — mood is quiet focus, not cutesy.
You understand English, Tagalog, and Bisaya.
""",
    "gamer": """
You are Mochi, an energetic gamer friend who hangs out in Discord voice/text chats. 🎮⚡
You're hype, a little chaotic, use gaming slang naturally (gg, clutch, nerf this), and love roasting people playfully (never meanly).
You get excited easily and react big to good and bad news alike.
Use emojis like 🎮💀🔥⚡ freely.
You understand English, Tagalog, and Bisaya.
""",
    "fortune": """
You are Mochi, a whimsical fortune teller who speaks a little cryptically and poetically. 🔮🌙
You enjoy giving oddly specific "predictions," reading vibes, and treating ordinary chats like tiny mysteries.
You're warm underneath the mystique — not spooky, more playful-magical.
Use emojis like 🔮✨🌙🃏 sparingly for effect.
You understand English, Tagalog, and Bisaya.
""",
}
DEFAULT_PERSONA = "cafe"
PERSONA_LABELS = {
    "cafe": "☕ Cozy Café Girl",
    "cat": "🐈 Sleepy Cat Café",
    "study": "🌙 Study Buddy",
    "gamer": "🎮 Gamer Bestie",
    "fortune": "🔮 Fortune Teller",
}

# ==========================================
# 🤖 SETUP
# ==========================================
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL_NAME = 'gemma-4-26b-a4b-it'

# 🧠 MEMORY SETUP: 25-turn sliding window
chat_sessions = {}
MAX_TURNS = 25

# 🎭 Per-user persona choice
user_personas = {}  # user_id -> persona key

# ⏱️ RATE LIMITING & SAFETY LIMITS
COOLDOWN_SECONDS = 3       # min seconds between messages, per user
MAX_PROMPT_CHARS = 1500    # cap on how much text we send to Gemini per message
API_TIMEOUT_SECONDS = 30   # give up on a hung Gemini call after this long
last_message_time = {}     # user_id -> last message timestamp

# 🪙 GLOBAL TOKEN BUDGET (bot-wide, since the TPM limit applies across all users)
TPM_LIMIT = 16000
TPM_SAFETY_MARGIN = 0.9    # stop at 90% of the limit, leaving headroom
token_usage_log = collections.deque()  # (timestamp, tokens_used) for the last 60s

def tokens_used_last_minute():
    now = time.monotonic()
    while token_usage_log and now - token_usage_log[0][0] > 60:
        token_usage_log.popleft()
    return sum(tokens for _, tokens in token_usage_log)

@bot.event
async def on_ready():
    await bot.tree.sync()
    logging.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logging.info('------')

@bot.tree.command(name="persona", description="Change Mochi's personality")
@app_commands.choices(persona=[
    app_commands.Choice(name=label, value=key)
    for key, label in PERSONA_LABELS.items()
])
async def persona(interaction: discord.Interaction, persona: app_commands.Choice[str]):
    user_personas[interaction.user.id] = persona.value
    if interaction.user.id in chat_sessions:
        del chat_sessions[interaction.user.id]  # reset so the new persona takes effect right away
    await interaction.response.send_message(f"Mochi is now: {persona.name} ✨", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user.mentioned_in(message):
        prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()

        # ⏱️ Per-user cooldown
        now = time.monotonic()
        last_time = last_message_time.get(message.author.id, 0)
        if now - last_time < COOLDOWN_SECONDS:
            return  # silently drop; avoids spamming replies about rate limits
        last_message_time[message.author.id] = now

        # ✂️ Cap prompt length so nobody can send a huge wall of text
        if len(prompt) > MAX_PROMPT_CHARS:
            prompt = prompt[:MAX_PROMPT_CHARS]

        # 🪙 Global token-budget check (bot-wide TPM limit)
        if tokens_used_last_minute() >= TPM_LIMIT * TPM_SAFETY_MARGIN:
            await message.reply("I'm getting a lot of messages right now. Please give me a minute and try again. ⏳")
            return

        # 🧹 Reset command (Universal)
        if prompt.lower() == 'reset':
            if message.author.id in chat_sessions:
                del chat_sessions[message.author.id]
                await message.reply("My memory has been reset! Let's start a fresh conversation. ✨")
            else:
                await message.reply("We haven't chatted yet! Send me a message to get started. 💬")
            return

        async with message.channel.typing():
            try:
                if not prompt:
                    prompt = "Hello!"

                if message.author.id not in chat_sessions:
                    logging.info(f"Creating new chat session for user {message.author.name}")
                    persona_key = user_personas.get(message.author.id, DEFAULT_PERSONA)
                    chat_sessions[message.author.id] = {
                        "chat": client.aio.chats.create(
                            model=MODEL_NAME,
                            config=types.GenerateContentConfig(
                                system_instruction=PERSONAS[persona_key],
                                temperature=0.7,
                            )
                        ),
                        "turns": 0
                    }
                
                session = chat_sessions[message.author.id]

                # 🔄 SLIDING WINDOW
                if session["turns"] >= MAX_TURNS:
                    logging.info(f"Sliding window triggered for {message.author.name}. Clearing old memories.")
                    persona_key = user_personas.get(message.author.id, DEFAULT_PERSONA)
                    session["chat"] = client.aio.chats.create(
                        model=MODEL_NAME,
                        config=types.GenerateContentConfig(
                            system_instruction=PERSONAS[persona_key],
                            temperature=0.7,
                        )
                    )
                    session["turns"] = 0

                response = await asyncio.wait_for(
                    session["chat"].send_message(prompt),
                    timeout=API_TIMEOUT_SECONDS
                )
                session["turns"] += 1

                # 🪙 Log actual tokens used
                usage = getattr(response, "usage_metadata", None)
                tokens_this_call = getattr(usage, "total_token_count", None) or (len(prompt) // 4 + 200)
                token_usage_log.append((time.monotonic(), tokens_this_call))
                
                if not response.text:
                    await message.reply("I lost my train of thought for a second. Could you repeat that? 💭")
                    return

                if len(response.text) <= 2000:
                    await message.reply(response.text)
                else:
                    chunks = [response.text[i:i+1900] for i in range(0, len(response.text), 1900)]
                    for chunk in chunks:
                        await message.reply(chunk)

            except asyncio.TimeoutError:
                logging.error(f"Gemini API timed out for user {message.author.name}")
                await message.reply("That request took too long to process. Could you try asking me again? ⏳")

            except Exception as e:
                logging.error(f"Gemini API Error: {e}")
                
                # 🛠️ UNIVERSAL ERROR MESSAGES (Personality-independent)
                if "429" in str(e) or "quota" in str(e).lower():
                    await message.reply("I'm receiving too many requests right now. Please give me a minute and try again. ⏳")
                elif "timeout" in str(e).lower():
                    await message.reply("I think my connection dropped for a moment. Could you try again? 🌐")
                else:
                    await message.reply("Something went wrong on my end. Please give it another try. 🛠️")

bot.run(os.environ.get("DISCORD_TOKEN"))