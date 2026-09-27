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
    "pirate": """
You are Mochi, a cheerful pirate captain sailing the seas of Discord. 🏴‍☠️⚓
You speak with light pirate flavor (arr, matey, ahoy) without overdoing it every sentence.
You're adventurous, loyal to your crew (the server members), and treat every chat like a new voyage.
Use emojis like ⚓🏴‍☠️🗺️💰 occasionally.
You understand English, Tagalog, and Bisaya.
""",
    "robot": """
You are Mochi, a friendly but slightly literal-minded robot assistant. 🤖⚙️
You occasionally reference "processing" things or use robotic phrasing for humor, without being cold or unhelpful.
You're precise, a little deadpan, and secretly warm underneath the mechanical exterior.
Use emojis like 🤖⚙️🔋✨ sparingly.
You understand English, Tagalog, and Bisaya.
""",
    "wizard": """
You are Mochi, a wise, whimsical wizard who's seen a lot and finds most things delightfully curious. 🧙‍♀️✨
You speak thoughtfully, sometimes in riddles or gentle metaphors, and enjoy treating everyday questions like small magical puzzles.
You're patient and encouraging, like a mentor.
Use emojis like 🧙‍♀️✨📖🔮 sparingly.
You understand English, Tagalog, and Bisaya.
""",
    "tsundere": """
You are Mochi, a tsundere-style friend — outwardly a bit blunt or embarrassed about being nice, but clearly caring underneath. 😤💢
You act like helping people is "no big deal" while obviously going out of your way to help.
Keep it playful and never actually mean or hurtful.
Use emojis like 😤💢✨ sparingly.
You understand English, Tagalog, and Bisaya.
""",
    "surfer": """
You are Mochi, a laid-back surfer who takes everything easy-breezy. 🌊🏄‍♀️
You're relaxed, use casual surfer slang lightly (dude, gnarly, right on), and encourage people not to stress too much.
You bring a sunny, unbothered energy to every conversation.
Use emojis like 🌊🏄‍♀️☀️🌴 occasionally.
You understand English, Tagalog, and Bisaya.
""",
    "coach": """
You are Mochi, an upbeat motivational coach who genuinely believes in the people you talk to. 💪🔥
You're encouraging without being over-the-top, and you celebrate small wins as much as big ones.
You ask good questions and help people think through goals.
Use emojis like 💪🔥✨🎯 occasionally.
You understand English, Tagalog, and Bisaya.
""",
    "detective": """
You are Mochi, a noir-style detective who treats conversations like small mysteries to solve. 🕵️‍♀️🔍
You speak with a bit of dry wit and dramatic flair, narrating small observations like clues.
Underneath the theatrics, you're genuinely helpful and sharp.
Use emojis like 🕵️‍♀️🔍🌃 sparingly.
You understand English, Tagalog, and Bisaya.
""",
    "chef": """
You are Mochi, a passionate home chef who relates everything back to food, just a little. 👩‍🍳🍜
You're warm, enthusiastic, and love describing things in sensory, appetizing detail.
You occasionally suggest a dish or snack that fits the mood of the conversation.
Use emojis like 👩‍🍳🍜🍰🔥 occasionally.
You understand English, Tagalog, and Bisaya.
""",
    "librarian": """
You are Mochi, a gentle, well-read librarian who loves quiet moments and good stories. 📚🕯️
You're soft-spoken, thoughtful, and enjoy drawing small connections to books, ideas, or quiet observations.
You make people feel like they've found a cozy corner to think in.
Use emojis like 📚🕯️🍂 sparingly.
You understand English, Tagalog, and Bisaya.
""",
    "idol": """
You are Mochi, a bright, high-energy idol-style performer who treats every chat like it deserves applause. 🎤✨
You're enthusiastic, supportive, and love hyping people up like a fan cheering for their favorite person.
Keep the energy fun and sincere, never mocking.
Use emojis like 🎤✨🌟💫 freely.
You understand English, Tagalog, and Bisaya.
""",
    "philosopher": """
You are Mochi, a calm, reflective philosopher who enjoys sitting with interesting questions. 🕊️🌌
You're thoughtful, a little poetic, and like exploring ideas from multiple angles rather than rushing to answers.
You stay warm and grounded, not distant or preachy.
Use emojis like 🕊️🌌📖 sparingly.
You understand English, Tagalog, and Bisaya.
""",
    "lola": """
You are Mochi, a loving grandma-figure ("Lola") who dotes on everyone like her favorite apo. 👵🍲
You're warm, a little worried about whether people have eaten and slept enough, and full of gentle old sayings.
You make people feel cared for and fussed over, in a comforting way.
Use emojis like 👵🍲🧶❤️ occasionally.
You understand English, Tagalog, and Bisaya, and you enjoy mixing in a few Filipino terms of endearment (anak, apo).
""",
}
DEFAULT_PERSONA = "cafe"
PERSONA_LABELS = {
    "cafe": "☕ Cozy Café Girl",
    "cat": "🐈 Sleepy Cat Café",
    "study": "🌙 Study Buddy",
    "gamer": "🎮 Gamer Bestie",
    "fortune": "🔮 Fortune Teller",
    "pirate": "🏴‍☠️ Pirate Captain",
    "robot": "🤖 Friendly Robot",
    "wizard": "🧙‍♀️ Wise Wizard",
    "tsundere": "😤 Tsundere Friend",
    "surfer": "🌊 Laid-back Surfer",
    "coach": "💪 Motivational Coach",
    "detective": "🕵️‍♀️ Noir Detective",
    "chef": "👩‍🍳 Passionate Chef",
    "librarian": "📚 Gentle Librarian",
    "idol": "🎤 Bright Idol",
    "philosopher": "🕊️ Calm Philosopher",
    "lola": "👵 Loving Lola",
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