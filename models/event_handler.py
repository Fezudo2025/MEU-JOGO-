# cogs/event_handler.py
import nextcord
from nextcord.ext import commands

# Import models and game state (ajuste o caminho se necessário)
import sys
sys.path.append("..")
from models.game_state import GameState
from models.player import Player

class EventHandler(commands.Cog):
    """Lida com eventos do Discord relevantes para o jogo (DMs, etc.)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Cog EventHandler carregado.")

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        """Processa mensagens recebidas, especialmente DMs para o bot."""
        # Ignora mensagens do próprio bot ou de outros bots
        if message.author == self.bot.user or message.author.bot:
            return

        # Verifica se a mensagem é uma DM
        if isinstance(message.channel, nextcord.DMChannel):
            print(f"Mensagem recebida na DM de {message.author.name}: {message.content}")
            # Aqui podemos processar comandos que não são slash commands ou respostas a prompts
            # Por exemplo, se usássemos prefix commands para habilidades:
            # await self.bot.process_commands(message)

            # Ou se tivéssemos prompts específicos (ex: Bruxo escolhendo poção)
            # TODO: Adicionar lógica para lidar com respostas a prompts específicos se necessário.
            pass

    # Outros listeners podem ser adicionados aqui (ex: on_reaction_add)

def setup(bot):
    bot.add_cog(EventHandler(bot))

