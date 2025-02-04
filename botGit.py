import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_ORG = os.getenv("GITHUB_ORG")

# Configurar permisos del bot
intents = discord.Intents.default()
intents.message_content = True
guilds = []  # Lista para guardar los servidores donde el bot está activo

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')
    for guild in bot.guilds:
        guilds.append(guild)
    await create_repo_channels()

async def create_repo_channels():
    url = f"https://api.github.com/orgs/{GITHUB_ORG}/repos?type=all"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        repos = response.json()
        for guild in guilds:
            existing_channels = [channel.name for channel in guild.text_channels]
            for repo in repos:
                repo_name = repo['name']
                if repo_name not in existing_channels:
                    channel = await guild.create_text_channel(repo_name)
                    await channel.send(f"📢 **Canal creado para el repositorio `{repo_name}`**")
                    await channel.send(view=RepoOptions(repo_name))
    else:
        print(f"❌ Error al obtener repositorios: {response.status_code}")

class RepoOptions(discord.ui.View):
    def __init__(self, repo_name):
        super().__init__()
        self.repo_name = repo_name
        self.add_item(RepoActionButton("Ver último commit", self.get_last_commit, repo_name))
        self.add_item(RepoActionButton("Ver cambios recientes", self.get_recent_changes, repo_name))
        self.add_item(RepoActionButton("Ver ramas disponibles", self.get_branches, repo_name))

    async def get_last_commit(self, interaction: discord.Interaction, repo_name):
        url = f"https://api.github.com/repos/{GITHUB_ORG}/{repo_name}/commits"
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            commit_data = response.json()[0]
            commit_info = (
                f"📌 **Último commit en {repo_name}:**\n"
                f"👤 **Autor:** {commit_data['commit']['author']['name']}\n"
                f"📝 **Mensaje:** {commit_data['commit']['message']}\n"
                f"🔗 [Ver en GitHub]({commit_data['html_url']})"
            )
            await interaction.response.send_message(commit_info)
        else:
            await interaction.response.send_message(f"❌ Error al obtener el último commit: {response.status_code}")
    
    async def get_recent_changes(self, interaction: discord.Interaction, repo_name):
        url = f"https://api.github.com/repos/{GITHUB_ORG}/{repo_name}/commits"
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            commits = response.json()[:5]
            changes_info = "\n".join([f"📝 {c['commit']['message']} - {c['commit']['author']['name']}" for c in commits])
            await interaction.response.send_message(f"📜 **Cambios recientes en {repo_name}:**\n{changes_info}")
        else:
            await interaction.response.send_message(f"❌ Error al obtener cambios recientes: {response.status_code}")

    async def get_branches(self, interaction: discord.Interaction, repo_name):
        url = f"https://api.github.com/repos/{GITHUB_ORG}/{repo_name}/branches"
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            branches = [b['name'] for b in response.json()]
            branches_info = "\n".join(branches)
            await interaction.response.send_message(f"🌿 **Ramas en {repo_name}:**\n{branches_info}")
        else:
            await interaction.response.send_message(f"❌ Error al obtener ramas: {response.status_code}")

class RepoActionButton(discord.ui.Button):
    def __init__(self, label, action, repo_name):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.action = action
        self.repo_name = repo_name

    async def callback(self, interaction: discord.Interaction):
        await self.action(interaction, self.repo_name)

@bot.event
async def on_guild_join(guild):
    guilds.append(guild)
    await create_repo_channels()

@bot.event
async def on_guild_remove(guild):
    guilds.remove(guild)

@bot.event
async def on_raw_github_event(payload):
    if payload['event'] == 'push':
        repo_name = payload['repository']['name']
        pusher = payload['pusher']['name']
        branch = payload['ref'].split('/')[-1]
        commit_msg = payload['head_commit']['message']

        if branch == "main":
            for guild in guilds:
                channel = discord.utils.get(guild.text_channels, name=repo_name)
                if channel:
                    await channel.send(f"🚀 **Push a `main` en `{repo_name}`**\n👤 **Autor:** {pusher}\n📝 **Mensaje:** {commit_msg}")

bot.run(DISCORD_TOKEN)
