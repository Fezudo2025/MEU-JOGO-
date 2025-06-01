# bot.py
import nextcord
import os
import asyncio
from nextcord.ext import commands

# --- Configuração Inicial ---
# TODO: Substituir "SEU_TOKEN_AQUI" pelo token real do bot.
# O token deve ser mantido em segredo. Considerar usar variáveis de ambiente.
BOT_TOKEN = MTM3ODQzMDc4MDA3ODAzNTEyNA.GpZOOo.liJjgVNK2AQbtNhpGSckho2lDX5F8Gy5FMRaZA

# Define as intenções (Intents) necessárias para o bot.
# Precisamos de guilds, members (para info de usuários), voice_states (para controle de voz) e messages/message_content (para DMs/comandos)
intents = nextcord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True # Necessário para ler conteúdo de DMs

# Cria a instância do bot
# Usaremos '!' como prefixo para comandos tradicionais, mas focaremos em Slash Commands
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Eventos do Bot ---
@bot.event
async def on_ready():
    """Evento chamado quando o bot está pronto e conectado ao Discord."""
    print(f'Bot conectado como {bot.user.name} (ID: {bot.user.id})')
    print('------')
    # Sincroniza os comandos de aplicativo (slash commands) com o Discord
    # try:
    #     synced = await bot.sync_application_commands()
    #     print(f"Sincronizados {len(synced)} comandos de aplicativo.")
    # except Exception as e:
    #     print(f"Falha ao sincronizar comandos: {e}")
    # Nota: A sincronização pode ser feita sob demanda ou ao carregar cogs.

# --- Carregamento de Módulos (Cogs) ---
# Lista inicial de cogs a serem carregados (nomes dos arquivos sem .py)
initial_extensions = [
    'cogs.game_manager', # Gerenciador principal do jogo
    'cogs.player_manager', # Gerenciador de jogadores
    'cogs.role_handler', # Lógica dos papéis
    'cogs.command_interface', # Comandos do usuário
    'cogs.event_handler', # Eventos específicos do jogo
    'cogs.voice_manager', # Controle de voz
    'cogs.timer_manager' # Controle de tempo
]

if __name__ == '__main__':
    # Cria os arquivos placeholder para os Cogs se não existirem
    # (Em um cenário real, esses arquivos teriam o código dos módulos)
    if not os.path.exists("cogs"):
        os.makedirs("cogs")
    for extension in initial_extensions:
        cog_path = extension.replace('.', '/') + '.py'
        if not os.path.exists(cog_path):
            with open(cog_path, 'w') as f:
                f.write(f"# {cog_path}\n")
                f.write("import nextcord\n")
                f.write("from nextcord.ext import commands\n\n")
                f.write(f"class {extension.split('.')[-1].capitalize().replace('_', '')}(commands.Cog):\n")
                f.write(f"    def __init__(self, bot):\n")
                f.write(f"        self.bot = bot\n\n")
                f.write(f"def setup(bot):\n")
                f.write(f"    bot.add_cog({extension.split('.')[-1].capitalize().replace('_', '')}(bot))\n")
            print(f"Arquivo placeholder criado: {cog_path}")

    # Carrega as extensões (Cogs)
    # for extension in initial_extensions:
    #     try:
    #         bot.load_extension(extension)
    #         print(f'Cog {extension} carregado com sucesso.')
    #     except Exception as e:
    #         print(f'Falha ao carregar cog {extension}: {e}')
    # Nota: O carregamento real será feito após a implementação dos cogs.

    # --- Execução do Bot ---
    # Verifica se o token foi definido
    if BOT_TOKEN == "SEU_TOKEN_AQUI":
        print("ERRO: O token do bot não foi definido em bot.py.")
        print("Por favor, substitua 'SEU_TOKEN_AQUI' pelo token real do seu bot.")
    else:
        # Inicia o bot
        # bot.run(BOT_TOKEN)
        # Nota: A execução real será feita em um passo posterior, após configuração e solicitação ao usuário.
        print("Estrutura básica do bot criada. A execução real requer o token.")
        print("Arquivos placeholder para Cogs criados em /home/ubuntu/cidade_dorme_bot/cogs/")


