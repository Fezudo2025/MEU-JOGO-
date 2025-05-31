# cogs/timer_manager.py
import nextcord
from nextcord.ext import commands, tasks
import asyncio
from typing import Callable, Coroutine, Any

# Import models (ajuste o caminho se necessário)
import sys
sys.path.append("..")
from models.game_state import GameState

class TimerManager(commands.Cog):
    """Gerencia os timers para as fases do jogo."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Cog TimerManager carregado.")

    async def start_phase_timer(self, game: GameState, duration: int, callback: Callable[[GameState], Coroutine[Any, Any, None]]):
        """Inicia um timer para uma fase do jogo.

        Args:
            game: O estado do jogo atual.
            duration: Duração do timer em segundos.
            callback: A função async a ser chamada quando o timer terminar.
        """
        # Cancela qualquer timer anterior para este jogo
        await game.cancel_phase_timer()

        print(f"Iniciando timer de {duration}s para a fase {game.game_phase} no servidor {game.guild.id}")

        # Cria a nova task do timer
        game.phase_timer_task = asyncio.create_task(self.timer_task(game, duration, callback))

    async def timer_task(self, game: GameState, duration: int, callback: Callable[[GameState], Coroutine[Any, Any, None]]):
        """A task que espera a duração e chama o callback."""
        try:
            await asyncio.sleep(duration)
            # Verifica se o jogo ainda está ativo e na fase esperada antes de chamar o callback
            # (Embora o cancelamento deva cuidar disso, é uma segurança extra)
            game_cog = self.bot.get_cog("GameManager")
            if game_cog and game.guild.id in game_cog.active_games and game == game_cog.get_game(game.guild.id):
                print(f"Timer de {duration}s concluído para {game.game_phase} no servidor {game.guild.id}. Chamando callback.")
                await callback(game)
            else:
                print(f"Timer de {duration}s concluído, mas o jogo {game.guild.id} não está mais ativo ou mudou. Callback não chamado.")
        except asyncio.CancelledError:
            print(f"Timer para {game.game_phase} no servidor {game.guild.id} foi cancelado.")
            # O cancelamento é esperado, não precisa fazer nada
            pass
        except Exception as e:
            print(f"Erro inesperado na task do timer para {game.guild.id}: {e}")
            # Tentar chamar o callback mesmo assim? Ou logar o erro?
            # Por segurança, talvez seja melhor não chamar o callback se houve erro inesperado.

    # Exemplo de como usar (será chamado pelo GameManager):
    # async def some_phase_start(self, game: GameState):
    #     timer_cog = self.bot.get_cog("TimerManager")
    #     if timer_cog:
    #         await timer_cog.start_phase_timer(game, 60, self.some_phase_end)
    #
    # async def some_phase_end(self, game: GameState):
    #     print(f"A fase {game.game_phase} terminou para o jogo {game.guild.id}")
    #     # ... lógica para a próxima fase ...

def setup(bot):
    bot.add_cog(TimerManager(bot))

