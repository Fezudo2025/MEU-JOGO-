# cogs/voice_manager.py
import nextcord
from nextcord.ext import commands
import asyncio
import os
import sys

# Import models (ajuste o caminho se necessário)
sys.path.append("..")
from models.game_state import GameState
from models.player import Player

class VoiceManager(commands.Cog):
    """Gerencia o controle de voz e áudio para o jogo Cidade Dorme."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_clients = {}  # guild_id -> voice_client
        print("Cog VoiceManager carregado e pronto para controlar o caos vocal!")
        
        # Caminhos para os arquivos de áudio
        self.audio_files = {
            'amanhecer': 'assets/audio/amanhecer.mp3',  # Som de galo cantando
            'anoitecer': 'assets/audio/anoitecer.mp3',  # Som de lobos uivando
            'assassinato': 'assets/audio/assassinato.mp3',  # Som de morte
            'reviver': 'assets/audio/reviver.mp3',  # Som angelical
            'tiro': 'assets/audio/tiro.mp3',  # Som de disparo
            'vitoria_palhaco': 'assets/audio/vitoria_palhaco.mp3',  # Som de palhaço
            'vitoria_cidade': 'assets/audio/vitoria_cidade.mp3',  # Som de vitória
            'vitoria_viloes': 'assets/audio/vitoria_viloes.mp3',  # Som de derrota
            'votacao': 'assets/audio/votacao.mp3',  # Som de votação
            'discussao': 'assets/audio/discussao.mp3',  # Som de discussão
            'vitoria_praga': 'assets/audio/vitoria_praga.mp3',  # Som de vitória da praga
            'vitoria_amantes': 'assets/audio/vitoria_amantes.mp3',  # Som de vitória dos amantes
            'vitoria_corruptor': 'assets/audio/vitoria_corruptor.mp3'  # Som de vitória do corruptor
        }
        
        # Cria a pasta de áudio se não existir
        os.makedirs('assets/audio', exist_ok=True)

    async def connect_to_voice(self, voice_channel):
        """Conecta ao canal de voz."""
        if not voice_channel:
            return None
            
        guild_id = voice_channel.guild.id
        
        # Se já estiver conectado, retorna o cliente existente
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_connected():
            return self.voice_clients[guild_id]
        
        # Tenta conectar ao canal de voz
        try:
            voice_client = await voice_channel.connect()
            self.voice_clients[guild_id] = voice_client
            return voice_client
        except Exception as e:
            print(f"Erro ao conectar ao canal de voz: {e}")
            return None

    async def disconnect_from_voice(self, guild_id):
        """Desconecta do canal de voz."""
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            if voice_client.is_connected():
                await voice_client.disconnect()
            del self.voice_clients[guild_id]

    async def play_sound(self, game: GameState, sound_type: str):
        """Reproduz um som específico no canal de voz."""
        if not game.voice_channel:
            return
            
        # Verifica se o arquivo de áudio existe
        if sound_type not in self.audio_files:
            print(f"Tipo de som '{sound_type}' não encontrado!")
            return
            
        audio_path = self.audio_files[sound_type]
        if not os.path.exists(audio_path):
            print(f"Arquivo de áudio '{audio_path}' não encontrado!")
            return
        
        # Conecta ao canal de voz
        voice_client = await self.connect_to_voice(game.voice_channel)
        if not voice_client:
            return
        
        # Reproduz o som
        try:
            # Verifica se já está tocando algo
            if voice_client.is_playing():
                voice_client.stop()
            
            # Reproduz o áudio
            voice_client.play(nextcord.FFmpegPCMAudio(audio_path))
            
            # Aguarda o término do áudio (opcional)
            while voice_client.is_playing():
                await asyncio.sleep(0.5)
                
        except Exception as e:
            print(f"Erro ao reproduzir áudio: {e}")

    async def mute_player(self, user):
        """Silencia um jogador no canal de voz."""
        if not user.voice:
            return
            
        try:
            await user.edit(mute=True)
        except Exception as e:
            print(f"Erro ao silenciar {user.name}: {e}")

    async def unmute_player(self, user):
        """Remove o silenciamento de um jogador no canal de voz."""
        if not user.voice:
            return
            
        try:
            await user.edit(mute=False)
        except Exception as e:
            print(f"Erro ao remover silenciamento de {user.name}: {e}")

    async def mute_all_in_channel(self, voice_channel):
        """Silencia todos os jogadores no canal de voz."""
        if not voice_channel:
            return
            
        for member in voice_channel.members:
            await self.mute_player(member)

    async def unmute_all_in_channel(self, voice_channel):
        """Remove o silenciamento de todos os jogadores no canal de voz."""
        if not voice_channel:
            return
            
        for member in voice_channel.members:
            await self.unmute_player(member)

    async def unmute_living_players(self, game: GameState):
        """Remove o silenciamento apenas dos jogadores vivos."""
        if not game.voice_channel:
            return
            
        for player in game.players.values():
            if player.status == 'vivo' and player.user.voice:
                await self.unmute_player(player.user)

# Função para adicionar o Cog ao bot
def setup(bot):
    bot.add_cog(VoiceManager(bot))
