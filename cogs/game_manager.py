# cogs/game_manager.py
import nextcord
from nextcord.ext import commands
import asyncio
import random
from typing import Dict, List, Optional, Tuple, Set
import os
import sys

# Import models (ajuste o caminho se necessário)
sys.path.append("..")
from models.game_state import GameState
from models.player import Player
from models.role import Role, get_all_roles, get_role_by_name

class GameManager(commands.Cog):
    """Gerencia o fluxo principal do jogo Cidade Dorme."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_games = {}  # guild_id -> GameState
        print("Cog GameManager carregado e pronto para a diversão!")
        
        # Frases humorísticas para diferentes fases do jogo
        self.night_start_messages = [
            "🌙 Silêncio, mortais! A noite chegou e com ela... a treta! Usem suas habilidades via DM. {time} minuto(s) no relógio! (Noite {night})",
            "🌙 Shhh! A cidade dorme (ou finge). É hora das ações na moita! Mandem ver nas DMs. Tic-tac, {time} minuto(s)! (Noite {night})",
            "🌙 Hora de fechar os olhinhos! Ou não, já que vocês estão lendo isso... Usem suas habilidades nas DMs! {time} minuto(s) e contando! (Noite {night})",
            "🌙 Noite {night}! Hora de aprontar nas sombras! Vilões, heróis e malucos, todos às DMs! {time} minuto(s) para a diversão noturna!",
            "🌙 Escuridão total! Hora de mandar mensagens suspeitas nas DMs. {time} minuto(s) para agir! (Noite {night})"
        ]
        
        self.day_start_messages = [
            "☀️ Acorda, cambada! O sol nasceu quadrado pra alguém? Resultados da noite em breve...",
            "☀️ Levantem e brilhem! Ou só levantem mesmo. Vamos descobrir as fofocas da madrugada.",
            "☀️ Dia {day}! Hora de ver quem não sobreviveu à balada de ontem! Resultados chegando...",
            "☀️ Olha o sol! Quem será que não vai mais sentir o calor dele? Resultados da carnificina em instantes!",
            "☀️ Amanheceu! Hora de contar os corpos e apontar dedos! Resultados da noite logo mais."
        ]
        
        self.discussion_start_messages = [
            "🗣️ Fogo no parquinho! Vocês têm {time} minutos pra lavar a roupa suja! Quem será o próximo a virar presunto?",
            "🗣️ Hora da gritaria organizada! {time} minutos para acusações, defesas e teorias da conspiração!",
            "🗣️ Aberta a sessão de dedos-duros! {time} minutos para convencer os outros de que você é inocente (mesmo não sendo)!",
            "🗣️ Tribunal da internet! {time} minutos para cancelar alguém antes que te cancelem primeiro!",
            "🗣️ Discussão liberada! {time} minutos para mostrar seus dotes de advogado ou de mentiroso profissional!"
        ]
        
        self.vote_start_messages = [
            "🗳️ Hora de votar! Quem vai pro saco hoje? Votem via DM com `/votar @jogador`!",
            "🗳️ Urnas abertas! Mandem suas cédulas via DM com `/votar @jogador`! Democracia a todo vapor!",
            "🗳️ Votação iniciada! Usem `/votar @jogador` na DM para escolher o azarado do dia!",
            "🗳️ Quem vai virar presunto? Votem via DM com `/votar @jogador`! Participem do BBB - Big Brother Burial!",
            "🗳️ Hora da sentença! Mandem seus votos via DM com `/votar @jogador`! Que vença o menos suspeito!"
        ]

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def preparar_jogo(self, ctx):
        """Prepara o jogo identificando jogadores, sorteando e distribuindo papéis."""
        # Verifica se já existe um jogo ativo neste servidor
        if ctx.guild.id in self.active_games:
            await ctx.send("❌ Já existe um jogo em andamento neste servidor! Finalize-o antes de iniciar outro.")
            return
            
        # Verifica se o autor está em um canal de voz
        if not ctx.author.voice:
            await ctx.send("❌ Você precisa estar em um canal de voz para iniciar o jogo!")
            return
            
        voice_channel = ctx.author.voice.channel
        
        # Conta os jogadores no canal de voz
        players_in_voice = [member for member in voice_channel.members if not member.bot]
        
        if len(players_in_voice) < 8:
            await ctx.send(f"❌ Número insuficiente de jogadores! Você tem {len(players_in_voice)}, mas precisa de pelo menos 8 jogadores no canal de voz.")
            return
            
        # Cria um novo estado de jogo
        game = GameState(
            game_channel=ctx.channel,
            voice_channel=voice_channel,
            host=ctx.author
        )
        
        # Adiciona os jogadores
        for member in players_in_voice:
            game.players[member.id] = Player(
                id=member.id,
                name=member.display_name,
                user=member
            )
        
        # Distribui os papéis
        await self.distribute_roles(game)
        
        # Registra o jogo como ativo
        self.active_games[ctx.guild.id] = game
        
        # Envia mensagem de confirmação
        await ctx.send(f"🎮 Jogo preparado com {len(game.players)} jogadores! Os papéis foram distribuídos via DM. Verifique se todos receberam seus papéis antes de iniciar a primeira noite com `/iniciar_noite`.")
        
        # Envia os papéis via DM
        await self.send_roles_dm(game)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def iniciar_noite(self, ctx):
        """Inicia a primeira noite do jogo após a preparação."""
        # Verifica se existe um jogo ativo neste servidor
        if ctx.guild.id not in self.active_games:
            await ctx.send("❌ Não há nenhum jogo preparado neste servidor! Use `/preparar_jogo` primeiro.")
            return
            
        game = self.active_games[ctx.guild.id]
        
        # Verifica se o jogo já começou
        if game.game_phase != 'setup':
            await ctx.send("❌ O jogo já está em andamento!")
            return
            
        # Inicia a primeira noite
        await ctx.send("🌙 Iniciando a primeira noite! Que comecem os jogos!")
        
        # Reproduz som de anoitecer
        voice_manager = self.bot.get_cog("VoiceManager")
        if voice_manager:
            await voice_manager.play_sound(game, 'anoitecer')
        
        # Inicia a primeira noite
        await self.start_first_night(game)

    async def distribute_roles(self, game: GameState):
        """Distribui os papéis para os jogadores."""
        # Obtém todos os papéis disponíveis
        all_roles = get_all_roles()
        
        # Determina quantos jogadores temos
        num_players = len(game.players)
        
        # Lista de prioridade dos papéis
        priority_roles = [
            "Prefeito", "Assassino Alfa", "Guarda-costas", "Anjo", "Detetive",
            "Assassino Júnior", "Cúmplice", "Xerife", "Palhaço", "Bruxo",
            "Fofoqueiro", "Vidente de Aura", "Médium", "Cupido", "A Praga", "Corruptor"
        ]
        
        # Seleciona os papéis baseado na prioridade e no número de jogadores
        selected_roles = []
        for role_name in priority_roles:
            if len(selected_roles) < num_players:
                role = get_role_by_name(role_name)
                if role:
                    selected_roles.append(role)
        
        # Embaralha os papéis
        random.shuffle(selected_roles)
        
        # Distribui os papéis para os jogadores
        players = list(game.players.values())
        for i, player in enumerate(players):
            if i < len(selected_roles):
                player.role = selected_roles[i]
            else:
                # Se houver mais jogadores que papéis, atribui papéis aleatórios da cidade
                city_roles = [r for r in all_roles if r.faction == "cidade" and r.name not in ["Prefeito", "Guarda-costas", "Anjo", "Detetive"]]
                if city_roles:
                    player.role = random.choice(city_roles)

    async def send_roles_dm(self, game: GameState):
        """Envia os papéis para os jogadores via DM."""
        command_interface = self.bot.get_cog("CommandInterface")
        
        for player_id, player in game.players.items():
            if not player.role:
                continue
                
            # Prepara a mensagem de DM com o papel do jogador
            role_name = player.role.name
            role_faction = player.role.faction
            role_description = player.role.description
            
            # Cria um embed com a imagem do papel
            embed = nextcord.Embed(
                title=f"{self._get_faction_emoji(role_faction)} {role_name} (Facção: {role_faction.capitalize()})",
                description=role_description,
                color=self._get_faction_color(role_faction)
            )
            
            # Adiciona campos com informações adicionais
            embed.add_field(
                name="Objetivo", 
                value=self._get_faction_objective(role_faction, role_name),
                inline=False
            )
            
            # Adiciona comandos específicos para o papel
            commands = self._get_role_commands(role_name)
            if commands:
                embed.add_field(
                    name="Comando", 
                    value=commands,
                    inline=False
                )
            
            # Adiciona a imagem do papel, se disponível
            if player.role.image_url:
                # Para uso com URLs de Discord CDN
                if player.role.image_url.startswith("http"):
                    embed.set_image(url=player.role.image_url)
                # Para uso com arquivos locais
                else:
                    file_path = os.path.join("/home/ubuntu/cidade_dorme_bot", player.role.image_url)
                    if os.path.exists(file_path):
                        file = nextcord.File(file_path, filename=os.path.basename(file_path))
                        embed.set_image(url=f"attachment://{os.path.basename(file_path)}")
                        try:
                            await player.user.send(
                                content="🤫 Segredinho nosso! Seu papel em Cidade Dorme é...",
                                embed=embed,
                                file=file
                            )
                            await asyncio.sleep(0.5)  # Pequeno delay para evitar rate limits
                            continue  # Pula o envio normal abaixo, já que enviamos com o arquivo
                        except Exception as e:
                            print(f"Erro ao enviar DM com imagem para {player.name}: {e}")
                            # Continua para tentar enviar sem a imagem
            
            # Envia a mensagem (sem imagem ou se falhou com imagem)
            try:
                await player.user.send(
                    content="🤫 Segredinho nosso! Seu papel em Cidade Dorme é...",
                    embed=embed
                )
                await asyncio.sleep(0.5)  # Pequeno delay para evitar rate limits
            except nextcord.Forbidden:
                await game.game_channel.send(f"⚠️ **ATENÇÃO**: Não consegui enviar DM para {player.user.mention}! Verifique suas configurações de privacidade e permita mensagens diretas de membros do servidor.")
                del game.players[player_id]  # Remove o jogador que não pode receber DMs
                if len(game.players) < 8:
                    await game.game_channel.send("❌ Não há jogadores suficientes para continuar (mínimo 8). Jogo cancelado.")
                    del self.active_games[game.game_channel.guild.id]
                    return
            except Exception as e:
                print(f"Erro ao enviar DM para {player.name}: {e}")
        
        # Envia informações adicionais para papéis específicos
        await self._send_special_role_info(game)

    async def _send_special_role_info(self, game: GameState):
        """Envia informações adicionais para papéis específicos."""
        # Prefeito recebe nomes do Anjo, Xerife e Cúmplice (sem saber quem é quem)
        prefeito = None
        anjo = None
        xerife = None
        cumplice = None
        
        # Encontra os jogadores com esses papéis
        for player in game.players.values():
            if not player.role:
                continue
                
            if player.role.name == "Prefeito":
                prefeito = player
            elif player.role.name == "Anjo":
                anjo = player
            elif player.role.name == "Xerife":
                xerife = player
            elif player.role.name == "Cúmplice":
                cumplice = player
        
        # Prefeito recebe informações
        if prefeito and anjo and xerife and cumplice:
            # Embaralha os três jogadores
            special_players = [anjo, xerife, cumplice]
            random.shuffle(special_players)
            
            # Envia a mensagem para o Prefeito
            special_names = [p.name for p in special_players]
            try:
                await prefeito.user.send(f"👁️ **Informação especial para o Prefeito**: Um destes jogadores é o Anjo, outro é o Xerife, e outro é o Cúmplice, mas você não sabe quem é quem: **{special_names[0]}**, **{special_names[1]}** e **{special_names[2]}**.")
            except Exception as e:
                print(f"Erro ao enviar informação especial para o Prefeito: {e}")
        
        # Anjo recebe nomes do Prefeito e Cúmplice (sem saber quem é quem)
        if anjo and prefeito and cumplice:
            # Embaralha os dois jogadores
            special_players = [prefeito, cumplice]
            random.shuffle(special_players)
            
            # Envia a mensagem para o Anjo
            special_names = [p.name for p in special_players]
            try:
                await anjo.user.send(f"👁️ **Informação especial para o Anjo**: Um destes jogadores é o Prefeito, e outro é o Cúmplice, mas você não sabe quem é quem: **{special_names[0]}** e **{special_names[1]}**.")
            except Exception as e:
                print(f"Erro ao enviar informação especial para o Anjo: {e}")
        
        # Vilões recebem informações sobre quem são os outros vilões
        viloes = [p for p in game.players.values() if p.role and p.role.faction == "vilões"]
        if len(viloes) > 1:
            for vilao in viloes:
                outros_viloes = [v.name for v in viloes if v != vilao]
                try:
                    await vilao.user.send(f"🔪 **Informação especial para os Vilões**: Seus parceiros do crime são: **{', '.join(outros_viloes)}**. Juntos vocês são imparáveis! (Ou não...)")
                except Exception as e:
                    print(f"Erro ao enviar informação sobre vilões para {vilao.name}: {e}")

    def _get_faction_emoji(self, faction: str) -> str:
        """Retorna o emoji correspondente à facção."""
        if faction.lower() == "cidade":
            return "🏙️"
        elif faction.lower() == "vilões":
            return "🔪"
        elif faction.lower() == "solo":
            return "🎭"
        return "❓"
    
    def _get_faction_color(self, faction: str) -> int:
        """Retorna a cor correspondente à facção para os embeds."""
        if faction.lower() == "cidade":
            return 0x3498db  # Azul
        elif faction.lower() == "vilões":
            return 0xe74c3c  # Vermelho
        elif faction.lower() == "solo":
            return 0xf1c40f  # Amarelo/Dourado
        return 0x95a5a6  # Cinza (neutro)
    
    def _get_faction_objective(self, faction: str, role_name: str) -> str:
        """Retorna o objetivo correspondente à facção ou papel específico."""
        if role_name == "Palhaço":
            return "Ser linchado durante o dia para vencer o jogo. Boa sorte convencendo os outros a te matarem!"
        elif role_name == "A Praga":
            return "Infectar todos os jogadores vivos para vencer o jogo. Espalhe sua doença sorrateiramente!"
        elif role_name == "Corruptor":
            return "Sobreviver até o final do jogo e garantir que o Prefeito esteja morto. Corrompa estrategicamente!"
        elif role_name == "Cupido":
            return "Formar um casal de Amantes e ajudar a Cidade a sobreviver. Se os Amantes sobreviverem até o final, eles também vencem!"
        
        if faction.lower() == "cidade":
            return "Eliminar todos os Vilões e Solos, e sobreviver. Use sua habilidade para ajudar a Cidade!"
        elif faction.lower() == "vilões":
            return "Eliminar o Prefeito e a maioria da Cidade. Trabalhe com os outros Vilões para dominar a cidade!"
        elif faction.lower() == "solo":
            return "Cumprir seu objetivo pessoal, independente das outras facções. Você joga sozinho!"
        return "Sobreviver e ajudar sua facção a vencer."
    
    def _get_role_commands(self, role_name: str) -> str:
        """Retorna os comandos específicos para cada papel."""
        commands = {
            "Prefeito": "Sua habilidade de anular o primeiro linchamento é automática.",
            "Guarda-costas": "`/habilidade proteger @jogador` (Use toda noite na DM)",
            "Detetive": "`/habilidade marcar_observar @jogador1 @jogador2` (Use toda noite na DM)",
            "Anjo": "`/habilidade reviver_uma_vez @jogador` (Use uma vez por jogo na DM)",
            "Xerife": "`/habilidade atirar @jogador` (Use durante o dia na DM, máximo 2 vezes no jogo)",
            "Assassino Alfa": "`/habilidade eliminar @jogador` (Use toda noite na DM)",
            "Assassino Júnior": "`/habilidade marcar_alvo_inicial @jogador` (Use na 1ª noite na DM)\n`/habilidade eliminar @jogador` (Use toda noite na DM)",
            "Cúmplice": "`/habilidade revelar_alvo_viloes @jogador` (Use na 1ª noite na DM)\n`/habilidade eliminar @jogador` (Use toda noite na DM)",
            "Bruxo": "`/habilidade usar_pocao vida @jogador` ou `/habilidade usar_pocao morte @jogador` (Use na DM, cada poção só uma vez)\n`/habilidade eliminar @jogador` (Use toda noite na DM)",
            "Fofoqueiro": "`/habilidade marcar_alvo_revelar @jogador` (Use na 1ª noite na DM)",
            "Vidente de Aura": "`/habilidade ver_aura @jogador` (Use toda noite na DM)",
            "Médium": "`/habilidade dar_voz_ao_morto @jogador_morto` (Use a partir da 2ª noite na DM)",
            "Cupido": "`/habilidade formar_casal @jogador1 @jogador2` (Use na 1ª noite na DM)",
            "A Praga": "`/habilidade infectar_inicial @jogador` (Use na 1ª noite na DM)\n`/habilidade exterminar_infectados` (Use uma vez por jogo na DM)",
            "Corruptor": "`/habilidade corromper @jogador` (Use toda noite na DM)",
            "Palhaço": "Não tem comandos especiais. Apenas tente ser linchado!"
        }
        
        return commands.get(role_name, "Sem comandos especiais.")

    async def start_first_night(self, game: GameState):
        """Inicia a primeira noite do jogo."""
        game.game_phase = 'night'
        game.night_number = 1
        
        # Silencia todos os jogadores
        voice_manager = self.bot.get_cog("VoiceManager")
        if voice_manager:
            await voice_manager.mute_all_in_channel(game.voice_channel)
        
        # Reproduz som de início da noite
        if voice_manager:
            await voice_manager.play_sound(game, 'anoitecer')
        
        # Envia mensagem de início da noite
        night_message = random.choice(self.night_start_messages).format(time=1, night=game.night_number)
        await game.game_channel.send(night_message)
        
        # Inicia o timer da noite
        timer_manager = self.bot.get_cog("TimerManager")
        if timer_manager:
            await timer_manager.start_night_timer(game, 60)  # 1 minuto para a primeira noite
        else:
            # Fallback se o TimerManager não estiver disponível
            await asyncio.sleep(60)
            await self.end_night(game)

    async def end_night(self, game: GameState):
        """Finaliza a noite e processa as ações noturnas."""
        if game.game_phase != 'night':
            return
            
        # Processa as ações noturnas
        role_handler = self.bot.get_cog("RoleHandler")
        if role_handler:
            await role_handler.process_night_actions(game)
        
        # Inicia o dia
        await self.start_day(game)

    async def start_day(self, game: GameState):
        """Inicia o dia após a noite."""
        game.game_phase = 'day_announcement'
        game.day_number += 1
        
        # Reproduz som de início do dia
        voice_manager = self.bot.get_cog("VoiceManager")
        if voice_manager:
            await voice_manager.play_sound(game, 'amanhecer')
        
        # Desmuta todos os jogadores vivos
        if voice_manager:
            await voice_manager.unmute_living_players(game)
            
            # Se o Médium escolheu um morto para falar, desmuta ele também
            if game.dead_speaker_id:
                dead_speaker = game.get_player(game.dead_speaker_id)
                if dead_speaker and dead_speaker.status == 'morto':
                    await voice_manager.unmute_player(dead_speaker.user)
        
        # Envia mensagem de início do dia
        day_message = random.choice(self.day_start_messages).format(day=game.day_number)
        await game.game_channel.send(day_message)
        
        # Pequena pausa para suspense
        await asyncio.sleep(3)
        
        # Anuncia os resultados da noite
        if not game.killed_tonight:
            await game.game_channel.send("Incrivelmente, ninguém morreu esta noite! Ou os assassinos são ruins, ou os protetores são bons demais. Ou ambos.")
        else:
            result_message = f"**Resultados Macabros da Noite {game.night_number}:**\n"
            for player_id, cause in game.killed_tonight.items():
                player = game.get_player(player_id)
                if player:
                    player.status = 'morto'
                    result_message += f"- {player.user.mention} (que era **{player.role.name}**) foi encontrado(a) morto(a). Causa da morte: **{cause}**. F.\n"
                    
                    # Reproduz som de morte
                    if voice_manager:
                        await voice_manager.play_sound(game, 'assassinato')
                        await asyncio.sleep(1)  # Pequena pausa entre sons
            
            await game.game_channel.send(result_message)
        
        # Limpa a lista de mortos da noite
        game.killed_tonight.clear()
        
        # Verifica condições de vitória
        if await self.check_win_conditions(game):
            return
            
        # Anuncia se o Médium deu voz a um morto
        if game.dead_speaker_id:
            dead_speaker = game.get_player(game.dead_speaker_id)
            if dead_speaker and dead_speaker.status == 'morto':
                await game.game_channel.send(f"👻 O Médium fez contato! O espírito de **{dead_speaker.user.mention}** pode falar durante esta discussão! Aproveitem (ou ignorem) a sabedoria (ou as reclamações) do além!")
        
        # Inicia a fase de discussão
        await self.start_discussion(game)

    async def start_discussion(self, game: GameState):
        """Inicia a fase de discussão do dia."""
        game.game_phase = 'day_discussion'
        
        # Reproduz som de início da discussão
        voice_manager = self.bot.get_cog("VoiceManager")
        if voice_manager:
            await voice_manager.play_sound(game, 'discussao')
        
        # Envia mensagem de início da discussão
        discussion_message = random.choice(self.discussion_start_messages).format(time=3)
        await game.game_channel.send(discussion_message)
        
        # Inicia o timer da discussão
        timer_manager = self.bot.get_cog("TimerManager")
        if timer_manager:
            await timer_manager.start_discussion_timer(game, 180)  # 3 minutos para discussão
        else:
            # Fallback se o TimerManager não estiver disponível
            await asyncio.sleep(180)
            await self.end_discussion(game)

    async def end_discussion(self, game: GameState):
        """Finaliza a fase de discussão e inicia a votação."""
        if game.game_phase != 'day_discussion':
            return
            
        # Inicia a fase de votação
        await self.start_voting(game)

    async def start_voting(self, game: GameState):
        """Inicia a fase de votação do dia."""
        game.game_phase = 'day_vote'
        game.votes.clear()  # Limpa votos anteriores
        
        # Reproduz som de início da votação
        voice_manager = self.bot.get_cog("VoiceManager")
        if voice_manager:
            await voice_manager.play_sound(game, 'votacao')
        
        # Envia mensagem de início da votação
        vote_message = random.choice(self.vote_start_messages)
        await game.game_channel.send(vote_message)
        
        # Envia prompts de votação para todos os jogadores vivos
        command_interface = self.bot.get_cog("CommandInterface")
        if command_interface:
            living_players = [p for p in game.players.values() if p.status == 'vivo']
            await command_interface.send_vote_prompts(game, living_players)
        
        # Inicia o timer da votação
        timer_manager = self.bot.get_cog("TimerManager")
        if timer_manager:
            await timer_manager.start_voting_timer(game, 60)  # 1 minuto para votação
        else:
            # Fallback se o TimerManager não estiver disponível
            await asyncio.sleep(60)
            await self.end_voting(game)

    async def end_voting(self, game: GameState):
        """Finaliza a fase de votação e processa os resultados."""
        if game.game_phase != 'day_vote':
            return
            
        # Conta os votos
        vote_counts = {}
        for voter_id, target_id in game.votes.items():
            voter = game.get_player(voter_id)
            target = game.get_player(target_id)
            
            # Verifica se o jogador é o Assassino Alfa (voto conta como 2)
            weight = 2 if voter and voter.role and voter.role.name == "Assassino Alfa" else 1
            
            if target_id in vote_counts:
                vote_counts[target_id] += weight
            else:
                vote_counts[target_id] = weight
        
        # Determina o jogador mais votado
        most_voted_id = None
        most_votes = 0
        tie = False
        
        for player_id, votes in vote_counts.items():
            if votes > most_votes:
                most_voted_id = player_id
                most_votes = votes
                tie = False
            elif votes == most_votes:
                tie = True
        
        # Anuncia os resultados da votação
        if tie or not most_voted_id:
            await game.game_channel.send("A votação terminou em empate ou ninguém recebeu votos! Ninguém será linchado hoje. Sorte de vocês!")
        else:
            most_voted = game.get_player(most_voted_id)
            
            # Verifica se é o Prefeito usando sua imunidade
            if most_voted.role.name == "Prefeito" and not most_voted.mayor_immunity_used:
                most_voted.mayor_immunity_used = True
                await game.game_channel.send(f"A cidade falou (ou gritou)! Com {most_votes} votos, **{most_voted.user.mention}** (que era **Prefeito**) foi linchado! Adeus!\n:shield: QUE REVIRAVOLTA! O Prefeito usou sua carta \"Saída Livre da Prisão\" e anulou o linchamento! Ele continua mandando (ou fingindo). Boa tentativa, galera!")
            else:
                # Marca o jogador como morto
                most_voted.status = 'morto'
                
                # Anuncia a morte
                await game.game_channel.send(f"A cidade falou (ou gritou)! Com {most_votes} votos, **{most_voted.user.mention}** (que era **{most_voted.role.name}**) foi linchado! Adeus!")
                
                # Verifica se é o Palhaço (vitória imediata)
                if most_voted.role.name == "Palhaço":
                    # Reproduz som de vitória do palhaço
                    voice_manager = self.bot.get_cog("VoiceManager")
                    if voice_manager:
                        await voice_manager.play_sound(game, 'vitoria_palhaco')
                    
                    await game.game_channel.send("**🏁 FIM DE JOGO! ACABOU A BRINCADEIRA! 🏁**\n\n🎭 O PALHAÇO VENCEU! Vocês caíram na pegadinha! Lincharam o Coringa da cidade. Vitória solo hilária!\n*Motivo: O Palhaço conseguiu ser linchado! Vitória solo hilária!*")
                    await self.end_game(game)
                    return
                
                # Verifica se o jogador linchado era um Amante
                if most_voted.lover:
                    lover = game.get_player(most_voted.lover.id)
                    if lover and lover.status == 'vivo':
                        lover.status = 'morto'
                        await game.game_channel.send(f"Oh, a tragédia! 💔 {most_voted.user.mention} morreu, e seu amor secreto, {lover.user.mention}, não aguentou a dor e morreu de coração partido! Que dramático!")
        
        # Muta o jogador morto (e seu amante, se aplicável)
        voice_manager = self.bot.get_cog("VoiceManager")
        if voice_manager:
            for player in game.players.values():
                if player.status == 'morto':
                    await voice_manager.mute_player(player.user)
        
        # Verifica condições de vitória
        if await self.check_win_conditions(game):
            return
            
        # Verifica se é o último dia (dia 7)
        if game.day_number >= 7:
            await self.handle_final_day(game)
            return
            
        # Inicia a próxima noite
        await self.start_night(game)

    async def handle_final_day(self, game: GameState):
        """Lida com o último dia (dia 7) e suas regras especiais."""
        await game.game_channel.send("**🌆 É O SÉTIMO DIA! O DESTINO DA CIDADE SERÁ DECIDIDO HOJE!**")
        
        # Verifica se o Prefeito e algum Vilão estão vivos
        prefeito_vivo = False
        vilao_vivo = False
        xerife_vivo = False
        xerife_tem_balas = False
        
        for player in game.players.values():
            if player.status != 'vivo':
                continue
                
            if player.role.name == "Prefeito":
                prefeito_vivo = True
            elif player.role.faction == "vilões":
                vilao_vivo = True
            elif player.role.name == "Xerife":
                xerife_vivo = True
                xerife_tem_balas = player.sheriff_bullets > 0
        
        # Se o Prefeito e algum Vilão estão vivos, o Xerife é obrigado a atirar
        if prefeito_vivo and vilao_vivo and xerife_vivo and xerife_tem_balas:
            xerife = next((p for p in game.players.values() if p.status == 'vivo' and p.role.name == "Xerife"), None)
            
            if xerife:
                # Reproduz som de tiro
                voice_manager = self.bot.get_cog("VoiceManager")
                if voice_manager:
                    await voice_manager.play_sound(game, 'tiro')
                
                await game.game_channel.send(f"**MOMENTO DECISIVO!** O Xerife {xerife.user.mention} é revelado e deve fazer um disparo final! O destino da cidade está em suas mãos!")
                
                # Força o Xerife a atirar
                # Isso seria implementado esperando a ação do Xerife
                # Por simplicidade, vamos apenas aguardar um tempo
                await asyncio.sleep(30)
                
                # Verifica se o Xerife atirou
                if game.sheriff_shot_today:
                    # O tiro já foi processado pelo RoleHandler
                    pass
                else:
                    await game.game_channel.send("O Xerife hesitou e não conseguiu atirar a tempo!")
        
        # Determina o vencedor final
        await self.determine_final_winner(game)

    async def determine_final_winner(self, game: GameState):
        """Determina o vencedor final no último dia."""
        # Verifica se o Prefeito e algum Vilão estão vivos
        prefeito_vivo = False
        vilao_vivo = False
        amantes_vivos = True
        corruptor_vivo = False
        
        for player in game.players.values():
            if player.status != 'vivo':
                continue
                
            if player.role.name == "Prefeito":
                prefeito_vivo = True
            elif player.role.faction == "vilões":
                vilao_vivo = True
            elif player.role.name == "Corruptor":
                corruptor_vivo = True
        
        # Verifica se os Amantes estão vivos
        if game.lovers:
            lover1_id, lover2_id = game.lovers
            lover1 = game.get_player(lover1_id)
            lover2 = game.get_player(lover2_id)
            
            amantes_vivos = (lover1 and lover2 and 
                            lover1.status == 'vivo' and 
                            lover2.status == 'vivo')
        else:
            amantes_vivos = False
        
        # Reproduz som apropriado para o vencedor
        voice_manager = self.bot.get_cog("VoiceManager")
        
        # Determina o vencedor
        if amantes_vivos:
            # Os Amantes vencem
            if voice_manager:
                await voice_manager.play_sound(game, 'vitoria_amantes')
                
            lover1 = game.get_player(game.lovers[0])
            lover2 = game.get_player(game.lovers[1])
            await game.game_channel.send(f"**🏁 FIM DE JOGO! ACABOU A BRINCADEIRA! 🏁**\n\n❤️ OS AMANTES VENCERAM! {lover1.user.mention} e {lover2.user.mention} sobreviveram juntos até o final! O amor triunfa sobre tudo!\n*Motivo: Os Amantes sobreviveram até o final do jogo!*")
        elif corruptor_vivo and not prefeito_vivo:
            # O Corruptor vence
            if voice_manager:
                await voice_manager.play_sound(game, 'vitoria_corruptor')
                
            corruptor = next((p for p in game.players.values() if p.status == 'vivo' and p.role.name == "Corruptor"), None)
            await game.game_channel.send(f"**🏁 FIM DE JOGO! ACABOU A BRINCADEIRA! 🏁**\n\n💰 O CORRUPTOR VENCEU! {corruptor.user.mention} conseguiu eliminar o Prefeito e sobreviver! A corrupção domina a cidade!\n*Motivo: O Corruptor sobreviveu e o Prefeito está morto!*")
        elif prefeito_vivo and not vilao_vivo:
            # A Cidade vence
            if voice_manager:
                await voice_manager.play_sound(game, 'vitoria_cidade')
                
            await game.game_channel.send("**🏁 FIM DE JOGO! ACABOU A BRINCADEIRA! 🏁**\n\n🏆 A CIDADE VENCEU! Os bonzinhos (ou nem tanto) eliminaram a escória! Podem comemorar (com moderação)!\n*Motivo: Todos os Vilões e Solos foram eliminados!*")
        elif vilao_vivo and not prefeito_vivo:
            # Os Vilões vencem
            if voice_manager:
                await voice_manager.play_sound(game, 'vitoria_viloes')
                
            await game.game_channel.send("**🏁 FIM DE JOGO! ACABOU A BRINCADEIRA! 🏁**\n\n🏆 OS VILÕES VENCERAM! A maldade triunfou! A cidade agora é deles. Fujam para as colinas!\n*Motivo: O Prefeito foi eliminado!*")
        else:
            # Empate ou situação indefinida
            await game.game_channel.send("**🏁 FIM DE JOGO! ACABOU A BRINCADEIRA! 🏁**\n\n🤝 EMPATE! Ninguém conseguiu cumprir seus objetivos completamente. A cidade continua em um impasse!\n*Motivo: Condições de vitória não foram atingidas por nenhuma facção!*")
        
        # Encerra o jogo
        await self.end_game(game)

    async def start_night(self, game: GameState):
        """Inicia uma nova noite."""
        game.game_phase = 'night'
        game.night_number += 1
        game.night_actions.clear()
        game.sheriff_shot_today = False
        
        # Reseta o jogador morto que pode falar (escolhido pelo Médium)
        if game.dead_speaker_id:
            voice_manager = self.bot.get_cog("VoiceManager")
            if voice_manager:
                dead_speaker = game.get_player(game.dead_speaker_id)
                if dead_speaker and dead_speaker.status == 'morto':
                    await voice_manager.mute_player(dead_speaker.user)
            
            game.dead_speaker_id = None
        
        # Silencia todos os jogadores
        voice_manager = self.bot.get_cog("VoiceManager")
        if voice_manager:
            await voice_manager.mute_all_in_channel(game.voice_channel)
        
        # Reproduz som de início da noite
        if voice_manager:
            await voice_manager.play_sound(game, 'anoitecer')
        
        # Envia mensagem de início da noite
        night_message = random.choice(self.night_start_messages).format(time=1, night=game.night_number)
        await game.game_channel.send(night_message)
        
        # Inicia o timer da noite
        timer_manager = self.bot.get_cog("TimerManager")
        if timer_manager:
            await timer_manager.start_night_timer(game, 60)  # 1 minuto para a noite
        else:
            # Fallback se o TimerManager não estiver disponível
            await asyncio.sleep(60)
            await self.end_night(game)

    async def check_win_conditions(self, game: GameState) -> bool:
        """Verifica as condições de vitória. Retorna True se o jogo acabou."""
        # Conta jogadores vivos por facção
        cidade_vivos = 0
        viloes_vivos = 0
        solos_vivos = 0
        prefeito_vivo = False
        
        for player in game.players.values():
            if player.status != 'vivo':
                continue
                
            if player.role.faction == "cidade":
                cidade_vivos += 1
                if player.role.name == "Prefeito":
                    prefeito_vivo = True
            elif player.role.faction == "vilões":
                viloes_vivos += 1
            elif player.role.faction == "solo":
                solos_vivos += 1
        
        # Verifica condições de vitória
        voice_manager = self.bot.get_cog("VoiceManager")
        
        # Verifica se a Praga venceu (todos os vivos estão infectados)
        praga_player = next((p for p in game.players.values() if p.role and p.role.name == "A Praga" and p.status == 'vivo'), None)
        if praga_player:
            all_infected = True
            for player in game.players.values():
                if player.status == 'vivo' and player != praga_player and player.id not in game.infected_players:
                    all_infected = False
                    break
            
            if all_infected and len(game.infected_players) > 0:
                if voice_manager:
                    await voice_manager.play_sound(game, 'vitoria_praga')
                    
                await game.game_channel.send(f"**🏁 FIM DE JOGO! ACABOU A BRINCADEIRA! 🏁**\n\n☣️ A PRAGA VENCEU! {praga_player.user.mention} infectou toda a cidade! A epidemia é total!\n*Motivo: Todos os jogadores vivos estão infectados!*")
                await self.end_game(game)
                return True
        
        # Verifica se o Corruptor venceu (Prefeito morto e Corruptor vivo)
        corruptor_player = next((p for p in game.players.values() if p.role and p.role.name == "Corruptor" and p.status == 'vivo'), None)
        if corruptor_player and not prefeito_vivo:
            if voice_manager:
                await voice_manager.play_sound(game, 'vitoria_corruptor')
                
            await game.game_channel.send(f"**🏁 FIM DE JOGO! ACABOU A BRINCADEIRA! 🏁**\n\n💰 O CORRUPTOR VENCEU! {corruptor_player.user.mention} conseguiu eliminar o Prefeito e sobreviver! A corrupção domina a cidade!\n*Motivo: O Corruptor sobreviveu e o Prefeito está morto!*")
            await self.end_game(game)
            return True
        
        # Verifica se os Amantes vencem (ambos vivos no final)
        if game.lovers:
            lover1_id, lover2_id = game.lovers
            lover1 = game.get_player(lover1_id)
            lover2 = game.get_player(lover2_id)
            
            if (lover1 and lover2 and 
                lover1.status == 'vivo' and 
                lover2.status == 'vivo' and
                viloes_vivos == 0 and solos_vivos == 0):
                
                if voice_manager:
                    await voice_manager.play_sound(game, 'vitoria_amantes')
                    
                await game.game_channel.send(f"**🏁 FIM DE JOGO! ACABOU A BRINCADEIRA! 🏁**\n\n❤️ OS AMANTES VENCERAM! {lover1.user.mention} e {lover2.user.mention} sobreviveram juntos até o final! O amor triunfa sobre tudo!\n*Motivo: Os Amantes sobreviveram até o final e todos os Vilões e Solos foram eliminados!*")
                await self.end_game(game)
                return True
        
        # Verifica se os Vilões venceram (Prefeito morto)
        if not prefeito_vivo and viloes_vivos > 0:
            if voice_manager:
                await voice_manager.play_sound(game, 'vitoria_viloes')
                
            await game.game_channel.send("**🏁 FIM DE JOGO! ACABOU A BRINCADEIRA! 🏁**\n\n🏆 OS VILÕES VENCERAM! A maldade triunfou! A cidade agora é deles. Fujam para as colinas!\n*Motivo: O Prefeito foi eliminado!*")
            await self.end_game(game)
            return True
        
        # Verifica se a Cidade venceu (todos os Vilões e Solos eliminados)
        if viloes_vivos == 0 and solos_vivos == 0 and cidade_vivos > 0:
            if voice_manager:
                await voice_manager.play_sound(game, 'vitoria_cidade')
                
            await game.game_channel.send("**🏁 FIM DE JOGO! ACABOU A BRINCADEIRA! 🏁**\n\n🏆 A CIDADE VENCEU! Os bonzinhos (ou nem tanto) eliminaram a escória! Podem comemorar (com moderação)!\n*Motivo: Todos os Vilões e Solos foram eliminados!*")
            await self.end_game(game)
            return True
        
        # Verifica se não há mais jogadores suficientes
        if cidade_vivos + viloes_vivos + solos_vivos < 2:
            await game.game_channel.send("**🏁 FIM DE JOGO! ACABOU A BRINCADEIRA! 🏁**\n\n⚰️ EXTINÇÃO! Quase todos morreram! Não há jogadores suficientes para continuar.\n*Motivo: Número insuficiente de jogadores vivos.*")
            await self.end_game(game)
            return True
        
        # O jogo continua
        return False

    async def end_game(self, game: GameState):
        """Encerra o jogo e limpa os recursos."""
        # Desmuta todos os jogadores
        voice_manager = self.bot.get_cog("VoiceManager")
        if voice_manager and game.voice_channel:
            await voice_manager.unmute_all_in_channel(game.voice_channel)
        
        # Envia mensagem final com resumo
        await game.game_channel.send("**Jogo encerrado! Obrigado por jogar Cidade Dorme!**\n\nPapéis dos jogadores:")
        
        # Lista todos os jogadores e seus papéis
        players_summary = ""
        for player in sorted(game.players.values(), key=lambda p: p.role.faction if p.role else ""):
            faction_emoji = self._get_faction_emoji(player.role.faction if player.role else "?")
            status_emoji = "❌" if player.status == 'morto' else "✅"
            players_summary += f"{status_emoji} {faction_emoji} **{player.name}**: {player.role.name if player.role else '?'}\n"
        
        # Divide a mensagem se for muito longa
        if len(players_summary) > 1900:
            chunks = [players_summary[i:i+1900] for i in range(0, len(players_summary), 1900)]
            for chunk in chunks:
                await game.game_channel.send(chunk)
        else:
            await game.game_channel.send(players_summary)
        
        # Desconecta do canal de voz
        if voice_manager:
            await voice_manager.disconnect_from_voice(game.game_channel.guild.id)
        
        # Remove o jogo da lista de jogos ativos
        if game.game_channel.guild.id in self.active_games:
            del self.active_games[game.game_channel.guild.id]

# Função para adicionar o Cog ao bot
def setup(bot):
    bot.add_cog(GameManager(bot))
