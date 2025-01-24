import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default() 
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents)  # Prefijo del bot

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

@bot.command()
async def hola(ctx):
    await ctx.send("¡Hola! 👋")

bot.run(token)
