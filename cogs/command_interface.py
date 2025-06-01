# cogs/command_interface.py
import nextcord
from nextcord.ext import commands
from typing import Dict, List, Optional
import asyncio
import random

# Import models (ajuste o caminho se necessário)
import sys
sys.path.append("..")
from models.game_state import GameState
from models.player import Player

# --- Funções Auxiliares de Mensagem --- 
async def send_dm_to_player(player: Player, message: str, embed: Optional[nextcord.Embed] = None, view: Optional[nextcord.ui.View] = None):
    """Envia uma DM para um jogador com tratamento de erro e humor (opcional)."""
    try:
        await player.user.send(content=message, embed=embed, view=view)
        print(f"  Mensagem enviada para {player.name}: {message[:50]}...")
        await asyncio.sleep(0.3) # Pequeno delay
    except nextcord.Forbidden:
        print(f"Erro: DM bloqueada para {player.name}. Talvez ele odeie robôs?")
        # TODO: Informar no canal principal?
    except Exception as e:
        print(f"Erro inesperado ao enviar DM para {player.name}: {e}")

# --- Classes de UI --- 
class VoteSelect(nextcord.ui.Select):
    """Menu de seleção para votação."""
    def __init__(self, game: GameState, voter: Player):
        self.game = game
        self.voter = voter
        options = [nextcord.SelectOption(label=p.name, value=str(p.id)) for p in game.get_living_players() if p != voter]
        super().__init__(placeholder="Escolha quem você quer linchar...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        target_id = int(self.values[0])
        target = self.game.get_player(target_id)
        
        if not target:
            await interaction.response.send_message("Erro: Jogador não encontrado. Tente novamente.", ephemeral=True)
            return
            
        self.game.add_vote(self.voter.id, target_id)
        await interaction.response.send_message(f"Voto computado! Você votou para linchar **{target.name}**. Agora é só torcer (ou não) para que a maioria concorde com você!", ephemeral=True)
        self.view.stop()

class VoteView(nextcord.ui.View):
    """View para votação."""
    def __init__(self, game: GameState, voter: Player):
        super().__init__(timeout=60) # 60 segundos para votar
        self.add_item(VoteSelect(game, voter))

class CommandInterface(commands.Cog):
    """Lida com comandos e interações do usuário. Agora com mais piadas ruins!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Cog CommandInterface carregado e pronto para receber ordens (ou não).")

    # --- Comandos Gerais ---
    @nextcord.slash_command(name="preparar_jogo", description="Prepara uma nova partida de Cidade Dorme (distribui papéis)")
    async def prepare_game_command(self, interaction: nextcord.Interaction):
        """Comando para preparar uma nova partida (distribuir papéis)."""
        guild_id = interaction.guild.id
        game_manager = self.bot.get_cog("GameManager")
        
        if not game_manager:
            await interaction.response.send_message("Erro interno: GameManager não encontrado. Chame o técnico!", ephemeral=True)
            return
            
        if guild_id in game_manager.active_games:
            await interaction.response.send_message("Calma, apressadinho! Já tem um jogo rolando. Termina esse primeiro ou use `/encerrar_jogo` para cancelar.", ephemeral=True)
            return

        if not isinstance(interaction.channel, nextcord.TextChannel):
            await interaction.response.send_message("Só começo a bagunça em canal de texto, beleza?", ephemeral=True)
            return

        if interaction.user.voice is None or interaction.user.voice.channel is None:
            await interaction.response.send_message("Pra jogar tem que estar no canal de voz, né gênio? Entra lá e tenta de novo.", ephemeral=True)
            return

        voice_channel = interaction.user.voice.channel
        members_in_voice = [m for m in voice_channel.members if not m.bot] # Ignora bots
        num_players = len(members_in_voice)

        if num_players < 8:
            await interaction.response.send_message(f"Ih, tá faltando gente! Precisa de pelo menos 8. Só tem {num_players} aí no {voice_channel.name}. Chama mais uns parças!", ephemeral=True)
            return
        if num_players > 16:
             await interaction.response.send_message(f"Eita, galera demais! O máximo é 16. Tem {num_players} aí no {voice_channel.name}. Expulsa uns aí!", ephemeral=True)
             return

        # Cria um novo estado de jogo
        game = GameState(interaction)
        game.voice_channel = voice_channel
        game_manager.active_games[guild_id] = game
        game.game_phase = 'preparing'

        await interaction.response.send_message(f"🥳 Preparando a partida de Cidade Dorme no canal de voz '{voice_channel.name}'! Distribuindo papéis secretos... (confiram as DMs!)")

        for member in members_in_voice:
            game.add_player(member)

        try:
            game.assign_roles()
        except ValueError as e:
            await interaction.followup.send(f"Deu ruim logo no começo: {e}. Jogo cancelado. Tentem de novo.")
            del game_manager.active_games[guild_id]
            return

        # Envia os papéis via DM
        await game_manager.send_roles_dm(game)

        # Se o envio de DMs não cancelou o jogo, avisa que está pronto para iniciar
        if guild_id in game_manager.active_games:
            await game.game_channel.send("Papéis distribuídos! Espero que ninguém tenha recebido o papel de 'trouxa'. 😜 Dêem uma lida rápida e quando todos estiverem prontos, usem /iniciar_noite para começar a primeira noite!")

    @nextcord.slash_command(name="iniciar_noite", description="Inicia a primeira noite após a preparação do jogo")
    async def start_night_command(self, interaction: nextcord.Interaction):
        """Comando para iniciar a primeira noite após a preparação."""
        guild_id = interaction.guild.id
        game_manager = self.bot.get_cog("GameManager")
        
        if not game_manager:
            await interaction.response.send_message("Erro interno: GameManager não encontrado. Chame o técnico!", ephemeral=True)
            return
            
        if guild_id not in game_manager.active_games:
            await interaction.response.send_message("Não tem nenhum jogo preparado! Use `/preparar_jogo` primeiro.", ephemeral=True)
            return
            
        game = game_manager.active_games[guild_id]
        
        if game.game_phase != 'preparing':
            await interaction.response.send_message("O jogo já começou ou não está na fase de preparação!", ephemeral=True)
            return
            
        await interaction.response.send_message("Que comece a diversão! Iniciando a primeira noite...")
        await game_manager.start_first_night(game)

    @nextcord.slash_command(name="encerrar_jogo", description="Encerra uma partida em andamento")
    async def end_game_command(self, interaction: nextcord.Interaction):
        """Comando para encerrar uma partida em andamento."""
        guild_id = interaction.guild.id
        game_manager = self.bot.get_cog("GameManager")
        
        if not game_manager:
            await interaction.response.send_message("Erro interno: GameManager não encontrado. Chame o técnico!", ephemeral=True)
            return
            
        if guild_id not in game_manager.active_games:
            await interaction.response.send_message("Não tem nenhum jogo rolando pra encerrar, tá viajando?", ephemeral=True)
            return
            
        game = game_manager.active_games[guild_id]
        
        # Confirma que é um admin ou o iniciador do jogo
        if not interaction.user.guild_permissions.administrator and interaction.user.id != game.players[list(game.players.keys())[0]].id:
            await interaction.response.send_message("Só admins ou quem iniciou o jogo podem encerrar a partida!", ephemeral=True)
            return
            
        await interaction.response.send_message("Jogo encerrado por comando administrativo. Todos os jogadores foram desmutados.")
        
        # Desmuta todos
        voice_cog = self.bot.get_cog("VoiceManager")
        if voice_cog and game.voice_channel:
            await voice_cog.unmute_all_in_channel(game.voice_channel)
            
        # Limpa o estado do jogo
        del game_manager.active_games[guild_id]

    # --- Comandos de Habilidade ---
    @nextcord.slash_command(name="habilidade", description="Usa uma habilidade do seu papel")
    async def ability_command(self, interaction: nextcord.Interaction):
        """Grupo de comandos para usar habilidades."""
        pass # Este é apenas um grupo, os subcomandos fazem o trabalho real

    @ability_command.subcommand(name="proteger", description="Guarda-costas: Protege um jogador durante a noite")
    async def protect_command(self, interaction: nextcord.Interaction, alvo: nextcord.Member):
        """Habilidade do Guarda-costas para proteger alguém."""
        await self._process_ability(interaction, "proteger", [alvo.id])

    @ability_command.subcommand(name="marcar_observar", description="Detetive: Marca dois jogadores para observar")
    async def observe_command(self, interaction: nextcord.Interaction, alvo1: nextcord.Member, alvo2: nextcord.Member):
        """Habilidade do Detetive para marcar dois jogadores."""
        await self._process_ability(interaction, "marcar_observar", [alvo1.id, alvo2.id])

    @ability_command.subcommand(name="reviver_uma_vez", description="Anjo: Revive um jogador (uso único)")
    async def revive_command(self, interaction: nextcord.Interaction, alvo: nextcord.Member):
        """Habilidade do Anjo para reviver alguém."""
        await self._process_ability(interaction, "reviver_uma_vez", [alvo.id])

    @ability_command.subcommand(name="atirar", description="Xerife: Atira em um jogador (durante o dia)")
    async def shoot_command(self, interaction: nextcord.Interaction, alvo: nextcord.Member):
        """Habilidade do Xerife para atirar em alguém."""
        await self._process_ability(interaction, "atirar", [alvo.id])

    @ability_command.subcommand(name="eliminar", description="Vilões: Vota para eliminar um jogador à noite")
    async def eliminate_command(self, interaction: nextcord.Interaction, alvo: nextcord.Member):
        """Habilidade dos Vilões para votar na eliminação."""
        await self._process_ability(interaction, "eliminar", [alvo.id])

    @ability_command.subcommand(name="marcar_alvo_inicial", description="Assassino Júnior: Marca alvo inicial (1ª noite)")
    async def mark_initial_target_command(self, interaction: nextcord.Interaction, alvo: nextcord.Member):
        """Habilidade do Assassino Júnior para marcar alvo inicial."""
        await self._process_ability(interaction, "marcar_alvo_inicial", [alvo.id])

    @ability_command.subcommand(name="revelar_alvo_viloes", description="Cúmplice: Revela papel de um jogador aos Vilões (1ª noite)")
    async def reveal_target_command(self, interaction: nextcord.Interaction, alvo: nextcord.Member):
        """Habilidade do Cúmplice para revelar papel aos Vilões."""
        await self._process_ability(interaction, "revelar_alvo_viloes", [alvo.id])

    @ability_command.subcommand(name="usar_pocao", description="Bruxo: Usa uma poção (vida ou morte)")
    async def use_potion_command(self, interaction: nextcord.Interaction, tipo: str, alvo: nextcord.Member):
        """Habilidade do Bruxo para usar poções."""
        if tipo.lower() not in ["vida", "morte"]:
            await interaction.response.send_message("Tipo de poção inválido! Use 'vida' ou 'morte'.", ephemeral=True)
            return
        await self._process_ability(interaction, "usar_pocao", [alvo.id], potion_type=tipo.lower())

    @ability_command.subcommand(name="marcar_alvo_revelar", description="Fofoqueiro: Marca alvo para revelar se morrer (1ª noite)")
    async def mark_reveal_target_command(self, interaction: nextcord.Interaction, alvo: nextcord.Member):
        """Habilidade do Fofoqueiro para marcar alvo de revelação."""
        await self._process_ability(interaction, "marcar_alvo_revelar", [alvo.id])

    @ability_command.subcommand(name="ver_aura", description="Vidente de Aura: Verifica se um jogador é da Cidade ou não")
    async def check_aura_command(self, interaction: nextcord.Interaction, alvo: nextcord.Member):
        """Habilidade do Vidente de Aura para verificar facção."""
        await self._process_ability(interaction, "ver_aura", [alvo.id])

    @ability_command.subcommand(name="dar_voz_ao_morto", description="Médium: Permite que um morto fale no próximo dia")
    async def speak_with_dead_command(self, interaction: nextcord.Interaction, alvo: nextcord.Member):
        """Habilidade do Médium para permitir que um morto fale."""
        await self._process_ability(interaction, "dar_voz_ao_morto", [alvo.id])

    @ability_command.subcommand(name="formar_casal", description="Cupido: Forma um casal de Amantes (1ª noite)")
    async def form_couple_command(self, interaction: nextcord.Interaction, alvo1: nextcord.Member, alvo2: nextcord.Member):
        """Habilidade do Cupido para formar um casal."""
        await self._process_ability(interaction, "formar_casal", [alvo1.id, alvo2.id])

    @ability_command.subcommand(name="infectar_inicial", description="A Praga: Infecta o paciente zero (1ª noite)")
    async def infect_initial_command(self, interaction: nextcord.Interaction, alvo: nextcord.Member):
        """Habilidade da Praga para infectar o paciente zero."""
        await self._process_ability(interaction, "infectar_inicial", [alvo.id])

    @ability_command.subcommand(name="exterminar_infectados", description="A Praga: Mata todos os infectados (uso único)")
    async def exterminate_infected_command(self, interaction: nextcord.Interaction):
        """Habilidade da Praga para exterminar infectados."""
        await self._process_ability(interaction, "exterminar_infectados", [])

    @ability_command.subcommand(name="corromper", description="Corruptor: Impede um jogador de usar habilidades")
    async def corrupt_command(self, interaction: nextcord.Interaction, alvo: nextcord.Member):
        """Habilidade do Corruptor para impedir uso de habilidades."""
        await self._process_ability(interaction, "corromper", [alvo.id])

    async def _process_ability(self, interaction: nextcord.Interaction, ability_name: str, target_ids: List[int], **kwargs):
        """Processa o uso de uma habilidade, verificando condições e registrando a ação."""
        # Verifica se é uma DM
        if interaction.guild is not None:
            await interaction.response.send_message("Psiu! Habilidades só podem ser usadas em mensagens privadas (DM)! Tenta de novo lá.", ephemeral=True)
            return

        # Busca o jogo ativo para este jogador
        game_manager = self.bot.get_cog("GameManager")
        if not game_manager:
            await interaction.response.send_message("Erro interno: GameManager não encontrado. Chame o técnico!", ephemeral=True)
            return

        player_id = interaction.user.id
        game = None
        for g in game_manager.active_games.values():
            if player_id in g.players:
                game = g
                break

        if not game:
            await interaction.response.send_message("Você não está em nenhum jogo ativo! Ou o jogo acabou, ou você não está participando.", ephemeral=True)
            return

        player = game.get_player(player_id)
        if not player:
            await interaction.response.send_message("Erro: Você não está registrado como jogador. Como isso aconteceu?", ephemeral=True)
            return

        if player.status != 'vivo':
            await interaction.response.send_message("Você está morto! Os mortos não podem usar habilidades... a menos que você seja um fantasma muito talentoso.", ephemeral=True)
            return

        # Verifica se o jogador tem o papel correto para a habilidade
        role_ability_map = {
            "proteger": ["Guarda-costas"],
            "marcar_observar": ["Detetive"],
            "reviver_uma_vez": ["Anjo"],
            "atirar": ["Xerife"],
            "eliminar": ["Assassino Alfa", "Assassino Júnior", "Cúmplice", "Bruxo"],
            "marcar_alvo_inicial": ["Assassino Júnior"],
            "revelar_alvo_viloes": ["Cúmplice"],
            "usar_pocao": ["Bruxo"],
            "marcar_alvo_revelar": ["Fofoqueiro"],
            "ver_aura": ["Vidente de Aura"],
            "dar_voz_ao_morto": ["Médium"],
            "formar_casal": ["Cupido"],
            "infectar_inicial": ["A Praga"],
            "exterminar_infectados": ["A Praga"],
            "corromper": ["Corruptor"]
        }

        allowed_roles = role_ability_map.get(ability_name, [])
        if not player.role or player.role.name not in allowed_roles:
            await interaction.response.send_message(f"Você não pode usar essa habilidade! Seu papel é {player.role.name if player.role else 'desconhecido'}.", ephemeral=True)
            return

        # Verifica fase do jogo
        day_abilities = ["atirar"]
        night_abilities = [a for a in role_ability_map.keys() if a not in day_abilities]
        
        if ability_name in day_abilities and game.game_phase not in ['day_discussion']:
            await interaction.response.send_message("Esta habilidade só pode ser usada durante o dia (fase de discussão)!", ephemeral=True)
            return
            
        if ability_name in night_abilities and game.game_phase != 'night':
            await interaction.response.send_message("Esta habilidade só pode ser usada durante a noite!", ephemeral=True)
            return

        # Verifica habilidades de primeira noite
        first_night_abilities = ["marcar_alvo_inicial", "revelar_alvo_viloes", "formar_casal", "infectar_inicial", "marcar_alvo_revelar"]
        if ability_name in first_night_abilities and game.night_number != 1:
            await interaction.response.send_message("Esta habilidade só pode ser usada na primeira noite!", ephemeral=True)
            return
            
        # Verifica habilidades que precisam de noites posteriores
        if ability_name == "dar_voz_ao_morto" and game.night_number < 2:
            await interaction.response.send_message("Esta habilidade só pode ser usada a partir da segunda noite!", ephemeral=True)
            return

        # Verifica uso único de habilidades
        if ability_name == "reviver_uma_vez" and player.angel_revive_used:
            await interaction.response.send_message("Você já usou sua habilidade de reviver! Só pode usar uma vez por jogo.", ephemeral=True)
            return
            
        if ability_name == "exterminar_infectados" and player.plague_exterminate_used:
            await interaction.response.send_message("Você já usou sua habilidade de extermínio! Só pode usar uma vez por jogo.", ephemeral=True)
            return
            
        if ability_name == "usar_pocao":
            potion_type = kwargs.get("potion_type", "")
            if potion_type == "vida" and player.witch_life_potion_used:
                await interaction.response.send_message("Você já usou sua poção da vida! Só pode usar uma vez por jogo.", ephemeral=True)
                return
            if potion_type == "morte" and player.witch_death_potion_used:
                await interaction.response.send_message("Você já usou sua poção da morte! Só pode usar uma vez por jogo.", ephemeral=True)
                return

        # Verifica alvos
        for target_id in target_ids:
            target = game.get_player(target_id)
            if not target:
                await interaction.response.send_message(f"Alvo inválido! Jogador não encontrado.", ephemeral=True)
                return
                
            # Verifica se o alvo está vivo (exceto para habilidades que afetam mortos)
            if ability_name != "dar_voz_ao_morto" and ability_name != "reviver_uma_vez" and target.status != 'vivo':
                await interaction.response.send_message(f"O alvo {target.name} já está morto! Escolha alguém vivo.", ephemeral=True)
                return
                
            # Verifica se o alvo está morto (para habilidades que afetam mortos)
            if ability_name == "dar_voz_ao_morto" and target.status != 'morto':
                await interaction.response.send_message(f"O alvo {target.name} está vivo! Você só pode dar voz a um jogador morto.", ephemeral=True)
                return
                
            # Verifica se o Guarda-costas não está tentando se proteger
            if ability_name == "proteger" and target_id == player_id:
                await interaction.response.send_message("Você não pode se proteger! Escolha outro jogador.", ephemeral=True)
                return
                
            # Verifica se o Guarda-costas não está repetindo proteção
            if ability_name == "proteger" and player.bodyguard_last_protected and player.bodyguard_last_protected.id == target_id:
                await interaction.response.send_message(f"Você não pode proteger {target.name} duas noites seguidas! Escolha outro jogador.", ephemeral=True)
                return

        # Verifica se o Cupido não está escolhendo a mesma pessoa duas vezes
        if ability_name == "formar_casal" and len(target_ids) == 2 and target_ids[0] == target_ids[1]:
            await interaction.response.send_message("Você não pode formar um casal com a mesma pessoa! Escolha dois jogadores diferentes.", ephemeral=True)
            return

        # Registra a ação
        game.add_night_action(player_id, ability_name, target_ids, **kwargs)
        
        # Responde com confirmação humorística
        target_names = []
        for tid in target_ids:
            target = game.get_player(tid)
            if target:
                target_names.append(target.name)
                
        target_str = ", ".join(target_names) if target_names else "ninguém"
        
        # Mensagens específicas por habilidade
        ability_messages = {
            "proteger": f"Você está protegendo {target_str} esta noite. Que herói! Ou só está fazendo seu trabalho mesmo...",
            "marcar_observar": f"Você está de olho em {target_str}. Sherlock Holmes ficaria orgulhoso (ou não).",
            "reviver_uma_vez": f"Você tentará reviver {target_str} se morrer esta noite. Dedos cruzados!",
            "atirar": f"BANG! Você atirou em {target_str}. Espero que tenha mirado direito!",
            "eliminar": f"Você votou para eliminar {target_str}. Que a maldade prevaleça!",
            "marcar_alvo_inicial": f"Se você morrer, {target_str} vai junto! Que amizade linda (e mortal).",
            "revelar_alvo_viloes": f"Você revelou o papel de {target_str} para os Vilões. Fofoca do mal!",
            "usar_pocao": f"Você usou a poção de {kwargs.get('potion_type', '?')} em {target_str}. Glup!",
            "marcar_alvo_revelar": f"Se você morrer, o papel de {target_str} será revelado. Última fofoca garantida!",
            "ver_aura": f"Você está verificando a aura de {target_str}. Será que é azul ou vermelha?",
            "dar_voz_ao_morto": f"Você deu voz ao espírito de {target_str} para o próximo dia. Ouija digital!",
            "formar_casal": f"Cupido atacou! {target_names[0]} e {target_names[1]} agora são um casal secreto. Que comece o drama!",
            "infectar_inicial": f"Você infectou {target_str} como paciente zero. Eca, que nojo!",
            "exterminar_infectados": "EXTERMÍNIO ATIVADO! Todos os infectados vão sentir o poder da Praga. Muahahaha!",
            "corromper": f"Você corrompeu {target_str}. Sem habilidades pra você hoje, colega!"
        }
        
        response_message = ability_messages.get(ability_name, f"Habilidade {ability_name} usada com sucesso em {target_str}!")
        await interaction.response.send_message(response_message, ephemeral=True)

    # --- Comando de Votação ---
    @nextcord.slash_command(name="votar", description="Vota para linchar um jogador durante o dia")
    async def vote_command(self, interaction: nextcord.Interaction, alvo: nextcord.Member):
        """Comando para votar no linchamento."""
        # Verifica se é uma DM
        if interaction.guild is not None:
            await interaction.response.send_message("Psiu! Votos só podem ser enviados em mensagens privadas (DM)! Tenta de novo lá.", ephemeral=True)
            return

        # Busca o jogo ativo para este jogador
        game_manager = self.bot.get_cog("GameManager")
        if not game_manager:
            await interaction.response.send_message("Erro interno: GameManager não encontrado. Chame o técnico!", ephemeral=True)
            return

        player_id = interaction.user.id
        game = None
        for g in game_manager.active_games.values():
            if player_id in g.players:
                game = g
                break

        if not game:
            await interaction.response.send_message("Você não está em nenhum jogo ativo! Ou o jogo acabou, ou você não está participando.", ephemeral=True)
            return

        player = game.get_player(player_id)
        if not player:
            await interaction.response.send_message("Erro: Você não está registrado como jogador. Como isso aconteceu?", ephemeral=True)
            return

        if player.status != 'vivo':
            await interaction.response.send_message("Você está morto! Os mortos não podem votar... a menos que você seja um fantasma muito democrático.", ephemeral=True)
            return

        # Verifica fase do jogo
        if game.game_phase != 'day_vote':
            await interaction.response.send_message("Não é hora de votar! Aguarde a fase de votação.", ephemeral=True)
            return

        # Verifica alvo
        target = game.get_player(alvo.id)
        if not target:
            await interaction.response.send_message(f"Alvo inválido! Jogador não encontrado.", ephemeral=True)
            return
            
        if target.status != 'vivo':
            await interaction.response.send_message(f"O alvo {target.name} já está morto! Escolha alguém vivo.", ephemeral=True)
            return

        # Registra o voto
        game.add_vote(player_id, alvo.id)
        
        # Responde com confirmação humorística
        await interaction.response.send_message(f"Voto computado! Você votou para linchar **{target.name}**. Agora é só torcer (ou não) para que a maioria concorde com você!", ephemeral=True)

    # --- Métodos para GameManager ---
    async def send_vote_prompts(self, game: GameState, players: List[Player]):
        """Envia prompts de votação para todos os jogadores vivos."""
        for player in players:
            # Opção 1: Usar o View com Select (mais bonito)
            view = VoteView(game, player)
            await send_dm_to_player(player, "É hora de votar! Escolha quem você quer linchar:", view=view)
            
            # Opção 2: Instrução para comando (fallback)
            living_players_mentions = [p.user.mention for p in game.get_living_players() if p != player]
            await send_dm_to_player(player, f"Alternativa: Use o comando `/votar @jogador` para votar. Jogadores vivos: {', '.join(living_players_mentions)}")

# Função para adicionar o Cog ao bot
def setup(bot):
    bot.add_cog(CommandInterface(bot))
