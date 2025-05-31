# cogs/player_manager.py
import nextcord
from nextcord.ext import commands

# Import models (ajuste o caminho se necessário)
import sys
sys.path.append("..")
from models.player import Player

class PlayerManager(commands.Cog):
    """Gerencia informações e comandos específicos de jogadores (se necessário)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Cog PlayerManager carregado.")

    # Poderia ter comandos como /meu_papel, /status_pessoal, etc.
    # Por enquanto, a maior parte da lógica está no GameState/GameManager.

def setup(bot):
    bot.add_cog(PlayerManager(bot))

