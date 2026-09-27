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

# 🧠 MEMORY SETUP: Store chat sessions per USER (not channel!)
chat_sessions = {}

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logging.info('------')

@bot.event
async def on_message(message):
    # 1. Ignore messages from bots
    if message.author.bot:
        return

    # 2. Only reply if the bot is mentioned
    if bot.user.mentioned_in(message):
        # Remove the mention from the prompt
        prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        # 3. Handle Reset Command
        if prompt.lower() == 'reset':
            if message.author.id in chat_sessions:
                del chat_sessions[message.author.id]
                await message.reply("Ehehe~! 🧹✨ I wiped my memory clean! Who are you again? Nice to meet you! 💖")
            else:
                await message.reply("I don't have any memories of you yet! Let's make some! >w< 🌸")
            return

        # Show typing indicator
        async with message.channel.typing():
            try:
                if not prompt:
                    prompt = "Hello!"

                # 4. Create a NEW chat session for this specific USER if it doesn't exist
                if message.author.id not in chat_sessions:
                    logging.info(f"Creating new chat session for user {message.author.name} ({message.author.id})")
                    chat_sessions[message.author.id] = client.chats.create(
                        model=MODEL_NAME,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION,
                            temperature=0.7,
                        )
                    )
                
                # Get the user's specific chat session
                chat = chat_sessions[message.author.id]

                # 5. Send the message
                response = await chat.send_message_async(prompt)
                
                if not response.text:
                    await message.reply("A-Ah! I was so happy I forgot what to say! What did you ask me? 🥺💦")
                    return

                # 6. Handle Discord's 2000 character limit
                if len(response.text) <= 2000:
                    await message.reply(response.text)
                else:
                    chunks = [response.text[i:i+1900] for i in range(0, len(response.text), 1900)]
                    for chunk in chunks:
                        await message.reply(chunk)

            except Exception as e:
                # 7. Smart Error Handling
                logging.error(f"Gemini API Error: {e}")
                
                if "429" in str(e) or "quota" in str(e).lower():
                    await message.reply("Wahhh! >w< You're chatting so fast that my poor little brain needs a tiny nap! 🥱💤 Please try again in a minute! 💖")
                elif "timeout" in str(e).lower():
                    await message.reply("O-Oh my! 🥺 I think I fell asleep waiting for the internet fairies! 🧚‍♀️✨ Can you poke me and try again? >w<")
                else:
                    await message.reply("Uwaaah! My sparkles got jumbled up! 😭✨ Give me another try, okay? 💕")

# Start the bot
bot.run(os.environ.get("DISCORD_TOKEN"))