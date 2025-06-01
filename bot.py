# bot.py
import nextcord
import os
from nextcord.ext import commands

# --- Carrega o token da variável de ambiente ---
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Intents necessários ---
intents = nextcord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True

# --- Criação do bot ---
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Evento: bot pronto ---
@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user.name} (ID: {bot.user.id})')
    print('------')

# --- Lista de extensões (Cogs) ---
initial_extensions = [
    'cogs.game_manager',
    'cogs.player_manager',
    'cogs.role_handler',
    'cogs.command_interface',
    'cogs.event_handler',
    'cogs.voice_manager',
    'cogs.timer_manager',
    'cogs.score_manager'
]

# --- Carrega os cogs ao iniciar ---
for extension in initial_extensions:
    try:
        bot.load_extension(extension)
        print(f'✅ Cog carregado: {extension}')
    except Exception as e:
        print(f'❌ Erro ao carregar {extension}: {e}')

# --- Executa o bot ---
if not BOT_TOKEN:
    print("❌ ERRO: A variável de ambiente BOT_TOKEN não está definida.")
else:
    bot.run(BOT_TOKEN)
