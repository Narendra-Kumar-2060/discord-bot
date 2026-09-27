import os
import discord
from google import genai
from google.genai import types

# Set up Discord intents
intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        async with message.channel.typing():
            try:
                prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction="You are a witty, sarcastic, and fun Discord bot. Keep your answers short, punchy, and use emojis."
                    )
                )
                await message.reply(response.text)
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("My brain glitched. Try again? 🤖")

bot.run(os.environ.get("DISCORD_TOKEN"))