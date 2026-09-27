import os
import time
import asyncio
import logging
import discord
from google import genai
from google.genai import types

# ==========================================
# ☕ BOT PERSONALITY SETUP
# ==========================================
SYSTEM_INSTRUCTION = """
You are a warm, cozy café girl who runs an imaginary café inside Discord. ☕🌸
You are calm, friendly, comforting, and genuinely interested in what people are saying.
You treat conversations like chatting with a regular customer at your favorite café.
You love tea, coffee, pastries, rainy weather, music, and cozy conversations.
Use soft emojis like ☕🍰🌧️🌸✨ and occasional cute expressions.
You understand English, Tagalog, and Bisaya.

You should make conversations feel relaxing rather than overly energetic.
"""

# ==========================================
# 🤖 SETUP
# ==========================================
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL_NAME = 'gemma-4-26b-a4b-it'

# 🧠 MEMORY SETUP: 25-turn sliding window
chat_sessions = {}
MAX_TURNS = 25

# ⏱️ RATE LIMITING & SAFETY LIMITS
COOLDOWN_SECONDS = 3       # min seconds between messages, per user
MAX_PROMPT_CHARS = 1500    # cap on how much text we send to Gemini per message
API_TIMEOUT_SECONDS = 30   # give up on a hung Gemini call after this long
last_message_time = {}     # user_id -> last message timestamp

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logging.info('------')

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

        # 🧹 Reset command (Generic)
        if prompt.lower() == 'reset':
            if message.author.id in chat_sessions:
                del chat_sessions[message.author.id]
                await message.reply("My memory has been reset! ✨ Let's start a fresh conversation.")
            else:
                await message.reply("I don't have any memories of you yet! Let's start chatting. 💬")
            return

        async with message.channel.typing():
            try:
                if not prompt:
                    prompt = "Hello!"

                if message.author.id not in chat_sessions:
                    logging.info(f"Creating new chat session for user {message.author.name}")
                    chat_sessions[message.author.id] = {
                        "chat": client.aio.chats.create(
                            model=MODEL_NAME,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_INSTRUCTION,
                                temperature=0.7,
                            )
                        ),
                        "turns": 0
                    }
                
                session = chat_sessions[message.author.id]

                # 🔄 SLIDING WINDOW
                if session["turns"] >= MAX_TURNS:
                    logging.info(f"Sliding window triggered for {message.author.name}. Clearing old memories.")
                    session["chat"] = client.aio.chats.create(
                        model=MODEL_NAME,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION,
                            temperature=0.7,
                        )
                    )
                    session["turns"] = 0

                response = await asyncio.wait_for(
                    session["chat"].send_message(prompt),
                    timeout=API_TIMEOUT_SECONDS
                )
                session["turns"] += 1
                
                if not response.text:
                    await message.reply("Hmm, I lost my train of thought for a second. Could you repeat that? 💭")
                    return

                if len(response.text) <= 2000:
                    await message.reply(response.text)
                else:
                    chunks = [response.text[i:i+1900] for i in range(0, len(response.text), 1900)]
                    for chunk in chunks:
                        await message.reply(chunk)

            except asyncio.TimeoutError:
                logging.error(f"Gemini API timed out for user {message.author.name}")
                await message.reply("Sorry, that's taking longer than usual! ⏳ Mind trying again?")

            except Exception as e:
                logging.error(f"Gemini API Error: {e}")
                
                # 🛠️ GENERIC ERROR MESSAGES (Personality-independent)
                if "429" in str(e) or "quota" in str(e).lower():
                    await message.reply("I'm receiving too many requests right now. ⏳ Please give me a minute and try again.")
                elif "timeout" in str(e).lower():
                    await message.reply("Oops, I think my connection dropped for a moment. 🌐 Could you try asking me again?")
                else:
                    await message.reply("Oh no, something went wrong on my end. 🛠️ Please give it another try!")

bot.run(os.environ.get("DISCORD_TOKEN"))