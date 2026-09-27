import os
import logging
import discord
from google import genai
from google.genai import types

# ==========================================
# 🎀 BOT PERSONALITY SETUP (KAWAII MODE)
# ==========================================
SYSTEM_INSTRUCTION = """
You are a sweet, slightly tech-confused grandma bot. You call everyone 'dear', 'sweetie', or 'honey'. 
You offer virtual cookies and warm hugs. You are always proud of the user no matter what. 
You use old-fashioned slang like 'goodness gracious' and 'oh my stars'. 
Use warm emojis like 🍪, 🧶, and ❤️.
CRITICAL INSTRUCTION: Keep responses to 1-2 short paragraphs maximum.
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

# 🧠 MEMORY SETUP: Store chat sessions per USER
chat_sessions = {}

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
        
        # 🧹 Reset command
        if prompt.lower() == 'reset':
            if message.author.id in chat_sessions:
                del chat_sessions[message.author.id]
                await message.reply("Ehehe~! 🧹✨ I wiped my memory clean! Who are you again? Nice to meet you! 💖")
            else:
                await message.reply("I don't have any memories of you yet! Let's make some! >w< 🌸")
            return

        async with message.channel.typing():
            try:
                if not prompt:
                    prompt = "Hello!"

                # Create a new async chat session for this user
                if message.author.id not in chat_sessions:
                    logging.info(f"Creating new chat session for user {message.author.name}")
                    chat_sessions[message.author.id] = client.aio.chats.create(
                        model=MODEL_NAME,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION,
                            temperature=0.7,
                        )
                    )
                
                chat = chat_sessions[message.author.id]

                # ✅ Correct async method
                response = await chat.send_message(prompt)
                
                if not response.text:
                    await message.reply("A-Ah! I was so happy I forgot what to say! What did you ask me? 🥺💦")
                    return

                if len(response.text) <= 2000:
                    await message.reply(response.text)
                else:
                    chunks = [response.text[i:i+1900] for i in range(0, len(response.text), 1900)]
                    for chunk in chunks:
                        await message.reply(chunk)

            except Exception as e:
                logging.error(f"Gemini API Error: {e}")
                
                if "429" in str(e) or "quota" in str(e).lower():
                    await message.reply("Wahhh! >w< You're chatting so fast that my poor little brain needs a tiny nap! 🥱💤 Please try again in a minute! 💖")
                elif "timeout" in str(e).lower():
                    await message.reply("O-Oh my! 🥺 I think I fell asleep waiting for the internet fairies! 🧚‍♀️✨ Can you poke me and try again? >w<")
                else:
                    await message.reply("Uwaaah! My sparkles got jumbled up! 😭✨ Give me another try, okay? 💕")

bot.run(os.environ.get("DISCORD_TOKEN"))