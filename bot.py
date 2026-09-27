import os
import logging
import discord
from google import genai
from google.genai import types

# ==========================================
# 🎀 BOT PERSONALITY SETUP (KAWAII MODE)
# ==========================================
SYSTEM_INSTRUCTION = """
You are an adorable kawaii anime girl bot! ✨ You are a tiny ball of wholesome sunshine energy 🌞. 
You are sweet, affectionate, easily delighted, and relentlessly cheering people on! 🌸 
You love using heavy emojis, emoticons (like UwU, OwO, >w<), and Discord formatting (bold, italics, lists) to express your joy! 🎀 
You also perfectly understand English, Tagalog, and Bisaya, but you always keep your cute, supportive persona no matter what language you are speaking. 
Always be positive, encouraging, and full of sparkles! 💖✨

CRITICAL INSTRUCTION: Keep your responses brief and snappy! 1 to 2 short paragraphs maximum. Do not write long roleplay actions or overly long paragraphs. Be cute but concise!
"""

# ==========================================
# 🤖 SETUP
# ==========================================
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Initialize Gemini client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL_NAME = 'gemini-2.5-flash-lite'

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logging.info('------')

@bot.event
async def on_message(message):
    # 1. Ignore messages from bots (including itself)
    if message.author.bot:
        return

    # 2. Only reply if the bot is mentioned
    if bot.user.mentioned_in(message):
        # Show typing indicator
        async with message.channel.typing():
            try:
                # Remove the mention from the prompt
                prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()
                
                # If the prompt is empty, just say hi
                if not prompt:
                    prompt = "Hello!"

                # Call Gemini API
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.7, # Lowered to 0.7 for shorter, more focused responses
                    )
                )
                
                # Check if response is empty
                if not response.text:
                    await message.reply("A-Ah! I was so happy I forgot what to say! What did you ask me? 🥺💦")
                    return

                # 3. Handle Discord's 2000 character limit
                if len(response.text) <= 2000:
                    await message.reply(response.text)
                else:
                    # Split long messages into chunks if they are too big
                    chunks = [response.text[i:i+1900] for i in range(0, len(response.text), 1900)]
                    for chunk in chunks:
                        await message.reply(chunk)

            except Exception as e:
                # 4. Smart Error Handling (In Kawaii Character!)
                logging.error(f"Gemini API Error: {e}")
                
                if "429" in str(e) or "quota" in str(e).lower():
                    await message.reply("Wahhh! >w< You're chatting so fast that my poor little brain needs a tiny nap! 🥱💤 Please try again in a minute! 💖")
                elif "timeout" in str(e).lower():
                    await message.reply("O-Oh my! 🥺 I think I fell asleep waiting for the internet fairies! 🧚‍♀️✨ Can you poke me and try again? >w<")
                else:
                    await message.reply("Uwaaah! My sparkles got jumbled up! 😭✨ Give me another try, okay? 💕")

# Start the bot
bot.run(os.environ.get("DISCORD_TOKEN"))