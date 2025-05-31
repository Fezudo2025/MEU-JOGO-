# cogs/role_handler.py
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

class RoleHandler(commands.Cog):
    """Processa as habilidades dos papéis no jogo Cidade Dorme."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Cog RoleHandler carregado e pronto para a magia!")
        
        # Frases humorísticas para feedback de ações
        self.action_success_messages = {
            "proteger": [
                "🛡️ Você está protegendo **{target}** como um verdadeiro guarda-costas! Nada vai passar por você... exceto talvez um segundo ataque!",
                "🛡️ **{target}** agora tem sua proteção! Você é praticamente o segurança VIP da balada!",
                "🛡️ Você se posicionou heroicamente na frente de **{target}**! Espero que valha a pena o sacrifício!"
            ],
            "marcar_observar": [
                "👁️ Você está de olho em **{target1}** e **{target2}**! Sherlock Holmes ficaria orgulhoso!",
                "👁️ Seus binóculos estão apontados para **{target1}** e **{target2}**! Se um deles morrer, você terá pistas!",
                "👁️ **{target1}** e **{target2}** estão sob sua vigilância! Detetive particular ou stalker? Você decide!"
            ],
            "reviver_uma_vez": [
                "😇 Você usou seu poder divino para trazer **{target}** de volta à vida! Agora você está sem mana para ressurreições!",
                "😇 **{target}** voltou dos mortos graças a você! Espero que ele(a) seja grato(a) e não desperdice essa segunda chance!",
                "😇 Milagre realizado! **{target}** está vivo(a) novamente! Seu poder de cura foi consumido, mas valeu a pena!"
            ],
            "atirar": [
                "🔫 BANG! Você atirou em **{target}**! Sua identidade como Xerife foi revelada para todos!",
                "🔫 Você puxou o gatilho contra **{target}**! Agora todos sabem que você é o Xerife da cidade!",
                "🔫 POW! Seu tiro acertou **{target}**! Sua estrela de Xerife agora brilha para todos verem!"
            ],
            "eliminar": [
                "🔪 Você votou para eliminar **{target}**! Que os outros vilões concordem com sua escolha sanguinária!",
                "🔪 **{target}** está na sua mira! Seu voto para assassiná-lo(a) foi registrado!",
                "🔪 Você escolheu **{target}** como vítima da noite! Agora é torcer para que seus comparsas concordem!"
            ],
            "marcar_alvo_inicial": [
                "🎯 Você marcou **{target}** como seu alvo inicial! Se você morrer, ele(a) vai junto para o além!",
                "🎯 **{target}** agora está ligado(a) ao seu destino! Se você cair, ele(a) cai também!",
                "🎯 Você e **{target}** agora têm uma conexão mortal! Se você for para o caixão, ele(a) te acompanha!"
            ],
            "revelar_alvo_viloes": [
                "🕵️ Você investigou **{target}** e revelou seu papel para os vilões! Informação é poder!",
                "🕵️ O papel de **{target}** foi exposto para todos os vilões! Agora vocês têm vantagem estratégica!",
                "🕵️ Seus comparsas agora sabem que **{target}** é **{role}**! Use essa informação com sabedoria!"
            ],
            "usar_pocao_vida": [
                "🧪 Você usou sua poção da vida em **{target}**! Ele(a) está protegido(a) esta noite!",
                "🧪 **{target}** bebeu sua poção mágica da vida! Qualquer ataque esta noite será neutralizado!",
                "🧪 Você derramou o elixir da vida em **{target}**! A morte não o(a) levará esta noite!"
            ],
            "usar_pocao_morte": [
                "☠️ Você envenenou **{target}** com sua poção da morte! Adeus, doce príncipe(sa)!",
                "☠️ **{target}** provou do seu veneno mortal! Não há antídoto para essa poção!",
                "☠️ Sua poção fatal foi servida a **{target}**! Os efeitos serão... bem, fatais!"
            ],
            "marcar_alvo_revelar": [
                "📣 Você marcou **{target}** para exposição! Se você morrer, o papel dele(a) será revelado para todos!",
                "📣 **{target}** está na sua lista de fofocas póstumas! Se você partir, seu segredo vai junto!",
                "📣 Você garantiu que se morrer, **{target}** terá seu papel exposto! Vingança do além!"
            ],
            "ver_aura": [
                "✨ Você viu a aura de **{target}**! Ela é **{aura_result}**!",
                "✨ As vibrações espirituais de **{target}** são **{aura_result}**!",
                "✨ Sua visão mística revelou que **{target}** tem aura **{aura_result}**!"
            ],
            "dar_voz_ao_morto": [
                "👻 Você estabeleceu contato com o espírito de **{target}**! Ele(a) poderá falar durante o próximo dia!",
                "👻 **{target}** recebeu sua conexão espiritual! A voz do além será ouvida amanhã!",
                "👻 Você sintonizou o canal do além! **{target}** poderá se comunicar com os vivos no próximo dia!"
            ],
            "formar_casal": [
                "❤️ Você uniu **{target1}** e **{target2}** como amantes! Que o amor floresça em meio ao caos!",
                "❤️ Suas flechas atingiram **{target1}** e **{target2}**! Eles agora são um casal apaixonado!",
                "❤️ **{target1}** e **{target2}** foram flechados! O amor é cego... e às vezes mortal neste jogo!"
            ],
            "infectar_inicial": [
                "🦠 Você infectou **{target}** como paciente zero! A epidemia começou!",
                "🦠 **{target}** foi contaminado(a) com sua praga! Agora é só esperar a infecção se espalhar!",
                "🦠 Sua doença foi transmitida para **{target}**! A contaminação da cidade começou!"
            ],
            "exterminar_infectados": [
                "☣️ Você ativou o extermínio! Todos os infectados cairão mortos!",
                "☣️ A fase terminal da sua praga foi ativada! Os infectados não sobreviverão!",
                "☣️ Você liberou a versão letal da sua doença! Adeus a todos os contaminados!"
            ],
            "corromper": [
                "💰 Você corrompeu **{target}** com sua influência! Ele(a) não poderá usar habilidades na próxima fase!",
                "💰 **{target}** sucumbiu à sua corrupção! Suas habilidades estão temporariamente neutralizadas!",
                "💰 Seu suborno silenciou **{target}**! Ele(a) está de mãos atadas na próxima fase!"
            ]
        }
        
        self.action_failure_messages = {
            "proteger": [
                "❌ Você não pode proteger **{target}**! Ou é você mesmo, ou você já protegeu essa pessoa antes!",
                "❌ Falha na proteção de **{target}**! Guarda-costas não podem se auto-proteger ou proteger o mesmo alvo duas vezes!",
                "❌ Proteção negada para **{target}**! Escolha outro alvo que você não tenha protegido antes (e que não seja você)!"
            ],
            "marcar_observar": [
                "❌ Você não pode observar esses alvos! Certifique-se de escolher dois jogadores diferentes e vivos!",
                "❌ Observação falhou! Você precisa escolher dois jogadores distintos que ainda estejam respirando!",
                "❌ Binóculos embaçados! Verifique se escolheu dois jogadores diferentes e que ainda estão vivos!"
            ],
            "reviver_uma_vez": [
                "❌ Você não pode reviver **{target}**! Ou a pessoa não está morta, ou você já usou seu poder, ou a pessoa não existe!",
                "❌ Ressurreição falhou! Verifique se o jogador está realmente morto e se você ainda tem seu poder!",
                "❌ Milagre negado! Você só pode reviver alguém que já esteja morto, e apenas uma vez no jogo!"
            ],
            "atirar": [
                "❌ Você não pode atirar em **{target}**! Ou a pessoa não existe, ou não está viva, ou você está sem balas!",
                "❌ Tiro falhou! Verifique se o alvo está vivo e se você ainda tem munição!",
                "❌ Gatilho travou! Você precisa de um alvo válido e ainda ter balas disponíveis!"
            ],
            "eliminar": [
                "❌ Você não pode eliminar **{target}**! Certifique-se de escolher um jogador vivo!",
                "❌ Eliminação falhou! O alvo precisa estar vivo para ser eliminado!",
                "❌ Ataque cancelado! Escolha um jogador que ainda esteja respirando!"
            ],
            "marcar_alvo_inicial": [
                "❌ Você não pode marcar **{target}** como alvo inicial! Ou a pessoa não existe, ou não está viva, ou você já marcou alguém!",
                "❌ Marcação falhou! Você só pode marcar um alvo vivo e apenas uma vez!",
                "❌ Alvo rejeitado! Verifique se o jogador existe, está vivo, e se você ainda não usou essa habilidade!"
            ],
            "revelar_alvo_viloes": [
                "❌ Você não pode revelar **{target}** aos vilões! Ou a pessoa não existe, ou não está viva, ou você já usou esse poder!",
                "❌ Revelação falhou! Você só pode revelar um jogador vivo e apenas uma vez!",
                "❌ Espionagem negada! Verifique se o alvo está vivo e se você ainda não usou essa habilidade!"
            ],
            "usar_pocao_vida": [
                "❌ Você não pode usar a poção da vida em **{target}**! Ou a pessoa não existe, ou não está viva, ou você já usou essa poção!",
                "❌ Poção da vida desperdiçada! Você só pode usá-la em um jogador vivo e apenas uma vez!",
                "❌ Elixir derramado! Verifique se o alvo está vivo e se você ainda tem essa poção!"
            ],
            "usar_pocao_morte": [
                "❌ Você não pode usar a poção da morte em **{target}**! Ou a pessoa não existe, ou não está viva, ou você já usou essa poção!",
                "❌ Poção da morte neutralizada! Você só pode usá-la em um jogador vivo e apenas uma vez!",
                "❌ Veneno ineficaz! Verifique se o alvo está vivo e se você ainda tem essa poção!"
            ],
            "marcar_alvo_revelar": [
                "❌ Você não pode marcar **{target}** para revelação! Ou a pessoa não existe, ou não está viva, ou você já marcou alguém!",
                "❌ Fofoca falhou! Você só pode marcar um alvo vivo e apenas uma vez!",
                "❌ Marcação rejeitada! Verifique se o jogador existe, está vivo, e se você ainda não usou essa habilidade!"
            ],
            "ver_aura": [
                "❌ Você não pode ver a aura de **{target}**! Ou a pessoa não existe, ou não está viva!",
                "❌ Visão mística falhou! O alvo precisa estar vivo para ter sua aura lida!",
                "❌ Terceiro olho embaçado! Escolha um jogador que ainda esteja entre os vivos!"
            ],
            "dar_voz_ao_morto": [
                "❌ Você não pode dar voz a **{target}**! Ou a pessoa não existe, ou não está morta!",
                "❌ Conexão espiritual falhou! Você só pode dar voz a alguém que já esteja morto!",
                "❌ Canalização negada! Verifique se o jogador existe e se já está no mundo dos mortos!"
            ],
            "formar_casal": [
                "❌ Você não pode formar um casal com **{target1}** e **{target2}**! Certifique-se de escolher dois jogadores diferentes e vivos!",
                "❌ Flechas do amor erraram o alvo! Você precisa escolher dois jogadores distintos que ainda estejam vivos!",
                "❌ Cupido fracassou! Verifique se escolheu dois jogadores diferentes e que ainda respiram!"
            ],
            "infectar_inicial": [
                "❌ Você não pode infectar **{target}**! Ou a pessoa não existe, ou não está viva, ou você já infectou alguém!",
                "❌ Infecção falhou! Você só pode infectar um alvo vivo e apenas uma vez!",
                "❌ Contágio bloqueado! Verifique se o jogador existe, está vivo, e se você ainda não usou essa habilidade!"
            ],
            "exterminar_infectados": [
                "❌ Você não pode exterminar os infectados agora! Ou não há infectados, ou você já usou esse poder!",
                "❌ Extermínio falhou! Você só pode usar essa habilidade uma vez e precisa haver infectados!",
                "❌ Praga contida! Verifique se há jogadores infectados e se você ainda não usou essa habilidade!"
            ],
            "corromper": [
                "❌ Você não pode corromper **{target}**! Ou a pessoa não existe, ou não está viva!",
                "❌ Corrupção falhou! O alvo precisa estar vivo para ser corrompido!",
                "❌ Suborno rejeitado! Escolha um jogador que ainda esteja entre os vivos!"
            ]
        }

    async def process_night_actions(self, game: GameState):
        """Processa todas as ações noturnas registradas."""
        # Primeiro, processa as ações de proteção
        await self._process_protection_actions(game)
        
        # Depois, processa as ações de observação
        await self._process_observation_actions(game)
        
        # Processa as ações de infecção inicial (Praga)
        await self._process_initial_infection(game)
        
        # Processa as ações de formação de casal (Cupido)
        await self._process_couple_formation(game)
        
        # Processa as ações de marcação de alvo (Assassino Júnior, Fofoqueiro)
        await self._process_target_marking(game)
        
        # Processa as ações de revelação (Cúmplice)
        await self._process_revelation_actions(game)
        
        # Processa as ações de dar voz aos mortos (Médium)
        await self._process_medium_actions(game)
        
        # Processa as ações de corrupção
        await self._process_corruption_actions(game)
        
        # Processa as ações de poções (Bruxo)
        await self._process_potion_actions(game)
        
        # Processa as ações de extermínio (Praga)
        await self._process_extermination_actions(game)
        
        # Por último, processa as ações de eliminação (Assassinos)
        await self._process_elimination_actions(game)
        
        # Verifica se há jogadores infectados que interagiram com outros
        await self._process_infection_spread(game)

    async def _process_protection_actions(self, game: GameState):
        """Processa as ações de proteção do Guarda-costas."""
        for player_id, actions in game.night_actions.items():
            for action in actions:
                if action["action"] == "proteger":
                    target_id = action["target_id"]
                    if target_id:
                        target = game.get_player(target_id)
                        if target:
                            target.protected_tonight = True
                            print(f"Jogador {target.name} protegido esta noite!")

    async def _process_observation_actions(self, game: GameState):
        """Processa as ações de observação do Detetive."""
        for player_id, actions in game.night_actions.items():
            for action in actions:
                if action["action"] == "marcar_observar":
                    target1_id = action["target1_id"]
                    target2_id = action["target2_id"]
                    if target1_id and target2_id:
                        # Registra a observação para verificar na próxima noite
                        game.detective_observations[player_id] = (target1_id, target2_id)
                        print(f"Detetive {player_id} está observando {target1_id} e {target2_id}!")

    async def _process_initial_infection(self, game: GameState):
        """Processa a infecção inicial da Praga."""
        for player_id, actions in game.night_actions.items():
            for action in actions:
                if action["action"] == "infectar_inicial":
                    target_id = action["target_id"]
                    if target_id and target_id not in game.infected_players:
                        game.infected_players.add(target_id)
                        print(f"Jogador {target_id} foi infectado pela Praga!")

    async def _process_couple_formation(self, game: GameState):
        """Processa a formação de casal pelo Cupido."""
        for player_id, actions in game.night_actions.items():
            for action in actions:
                if action["action"] == "formar_casal":
                    target1_id = action["target1_id"]
                    target2_id = action["target2_id"]
                    if target1_id and target2_id:
                        # Registra o casal
                        game.lovers = (target1_id, target2_id)
                        
                        # Atualiza os jogadores para saberem que são amantes
                        lover1 = game.get_player(target1_id)
                        lover2 = game.get_player(target2_id)
                        
                        if lover1 and lover2:
                            lover1.lover = lover2
                            lover2.lover = lover1
                            
                            # Envia mensagens para os amantes
                            try:
                                await lover1.user.send(f"💘 **Você foi flechado pelo Cupido!** Você está secretamente apaixonado(a) por **{lover2.name}**. Seu objetivo agora é sobreviverem juntos até o final. Se um de vocês morrer, o outro morrerá de coração partido!")
                                await lover2.user.send(f"💘 **Você foi flechado pelo Cupido!** Você está secretamente apaixonado(a) por **{lover1.name}**. Seu objetivo agora é sobreviverem juntos até o final. Se um de vocês morrer, o outro morrerá de coração partido!")
                            except Exception as e:
                                print(f"Erro ao enviar mensagem para os amantes: {e}")
                            
                            print(f"Cupido formou um casal entre {lover1.name} e {lover2.name}!")

    async def _process_target_marking(self, game: GameState):
        """Processa as marcações de alvo do Assassino Júnior e Fofoqueiro."""
        for player_id, actions in game.night_actions.items():
            player = game.get_player(player_id)
            if not player:
                continue
                
            for action in actions:
                if action["action"] == "marcar_alvo_inicial" and player.role.name == "Assassino Júnior":
                    target_id = action["target_id"]
                    if target_id:
                        player.marked_target = target_id
                        print(f"Assassino Júnior {player.name} marcou {target_id} como alvo!")
                
                elif action["action"] == "marcar_alvo_revelar" and player.role.name == "Fofoqueiro":
                    target_id = action["target_id"]
                    if target_id:
                        player.marked_target = target_id
                        print(f"Fofoqueiro {player.name} marcou {target_id} para revelação!")

    async def _process_revelation_actions(self, game: GameState):
        """Processa as ações de revelação do Cúmplice."""
        for player_id, actions in game.night_actions.items():
            for action in actions:
                if action["action"] == "revelar_alvo_viloes":
                    target_id = action["target_id"]
                    if target_id:
                        target = game.get_player(target_id)
                        if not target:
                            continue
                            
                        # Envia mensagem para todos os vilões
                        viloes = [p for p in game.players.values() if p.role and p.role.faction == "vilões"]
                        for vilao in viloes:
                            try:
                                await vilao.user.send(f"🕵️ **Informação do Cúmplice:** {target.name} é **{target.role.name}**!")
                            except Exception as e:
                                print(f"Erro ao enviar revelação para vilão {vilao.name}: {e}")
                        
                        print(f"Cúmplice revelou {target.name} ({target.role.name}) para os vilões!")

    async def _process_medium_actions(self, game: GameState):
        """Processa as ações do Médium para dar voz aos mortos."""
        for player_id, actions in game.night_actions.items():
            for action in actions:
                if action["action"] == "dar_voz_ao_morto":
                    target_id = action["target_id"]
                    if target_id:
                        target = game.get_player(target_id)
                        if target and target.status == 'morto':
                            game.dead_speaker_id = target_id
                            print(f"Médium deu voz ao morto {target.name} para o próximo dia!")

    async def _process_corruption_actions(self, game: GameState):
        """Processa as ações de corrupção."""
        for player_id, actions in game.night_actions.items():
            for action in actions:
                if action["action"] == "corromper":
                    target_id = action["target_id"]
                    if target_id:
                        target = game.get_player(target_id)
                        if target:
                            target.corrupted = True
                            print(f"Jogador {target.name} foi corrompido!")

    async def _process_potion_actions(self, game: GameState):
        """Processa as ações de poções do Bruxo."""
        for player_id, actions in game.night_actions.items():
            player = game.get_player(player_id)
            if not player or player.role.name != "Bruxo":
                continue
                
            for action in actions:
                if action["action"] == "usar_pocao_vida":
                    target_id = action["target_id"]
                    if target_id and not player.life_potion_used:
                        target = game.get_player(target_id)
                        if target:
                            target.protected_tonight = True
                            player.life_potion_used = True
                            print(f"Bruxo usou poção da vida em {target.name}!")
                
                elif action["action"] == "usar_pocao_morte":
                    target_id = action["target_id"]
                    if target_id and not player.death_potion_used:
                        target = game.get_player(target_id)
                        if target and target.status == 'vivo' and not target.protected_tonight:
                            game.killed_tonight[target_id] = "Poção da Morte do Bruxo"
                            player.death_potion_used = True
                            print(f"Bruxo usou poção da morte em {target.name}!")

    async def _process_extermination_actions(self, game: GameState):
        """Processa as ações de extermínio da Praga."""
        for player_id, actions in game.night_actions.items():
            player = game.get_player(player_id)
            if not player or player.role.name != "A Praga":
                continue
                
            for action in actions:
                if action["action"] == "exterminar_infectados" and not player.extermination_used:
                    # Mata todos os infectados que não estão protegidos
                    for infected_id in game.infected_players:
                        infected = game.get_player(infected_id)
                        if infected and infected.status == 'vivo' and not infected.protected_tonight:
                            game.killed_tonight[infected_id] = "Extermínio da Praga"
                    
                    player.extermination_used = True
                    print("A Praga ativou o extermínio dos infectados!")
                    
                    # Verifica se todos os vivos estão infectados (condição de vitória)
                    await self._check_plague_win_condition(game)

    async def _process_elimination_actions(self, game: GameState):
        """Processa as ações de eliminação dos Assassinos."""
        # Conta os votos para cada alvo
        elimination_votes = {}
        
        for player_id, actions in game.night_actions.items():
            player = game.get_player(player_id)
            if not player or player.role.faction != "vilões":
                continue
                
            for action in actions:
                if action["action"] == "eliminar":
                    target_id = action["target_id"]
                    if target_id:
                        # Verifica se o jogador é o Assassino Alfa (voto conta como 2)
                        weight = 2 if player.role.name == "Assassino Alfa" else 1
                        
                        if target_id in elimination_votes:
                            elimination_votes[target_id] += weight
                        else:
                            elimination_votes[target_id] = weight
        
        # Determina o alvo mais votado
        most_voted_id = None
        most_votes = 0
        
        for target_id, votes in elimination_votes.items():
            if votes > most_votes:
                most_voted_id = target_id
                most_votes = votes
        
        # Elimina o alvo mais votado, se não estiver protegido
        if most_voted_id:
            target = game.get_player(most_voted_id)
            if target and target.status == 'vivo' and not target.protected_tonight:
                game.killed_tonight[most_voted_id] = "Vilões Malvados"
                print(f"Os vilões eliminaram {target.name}!")

    async def _process_infection_spread(self, game: GameState):
        """Processa a propagação da infecção da Praga."""
        # Verifica todas as interações da noite
        new_infections = set()
        
        for player_id, actions in game.night_actions.items():
            # Se o jogador está infectado, infecta seus alvos
            if player_id in game.infected_players:
                for action in actions:
                    if "target_id" in action and action["target_id"]:
                        new_infections.add(action["target_id"])
                    if "target1_id" in action and action["target1_id"]:
                        new_infections.add(action["target1_id"])
                    if "target2_id" in action and action["target2_id"]:
                        new_infections.add(action["target2_id"])
            
            # Se o jogador interagiu com um infectado, ele também fica infectado
            for action in actions:
                if "target_id" in action and action["target_id"] in game.infected_players:
                    new_infections.add(player_id)
                if "target1_id" in action and action["target1_id"] in game.infected_players:
                    new_infections.add(player_id)
                if "target2_id" in action and action["target2_id"] in game.infected_players:
                    new_infections.add(player_id)
        
        # Adiciona as novas infecções
        game.infected_players.update(new_infections)
        
        # Verifica se todos os vivos estão infectados (condição de vitória)
        if new_infections:
            await self._check_plague_win_condition(game)

    async def _check_plague_win_condition(self, game: GameState):
        """Verifica se a Praga venceu (todos os vivos estão infectados)."""
        praga_player = next((p for p in game.players.values() if p.role and p.role.name == "A Praga" and p.status == 'vivo'), None)
        if not praga_player:
            return False
            
        all_infected = True
        for player in game.players.values():
            if player.status == 'vivo' and player != praga_player and player.id not in game.infected_players:
                all_infected = False
                break
        
        return all_infected and len(game.infected_players) > 0

    async def handle_role_action(self, ctx, action, **kwargs):
        """Processa uma ação de papel solicitada por um jogador."""
        # Verifica se o jogador está em um jogo ativo
        game_manager = self.bot.get_cog("GameManager")
        if not game_manager:
            await ctx.send("❌ Sistema de jogo não disponível!")
            return
            
        game = None
        for g in game_manager.active_games.values():
            if ctx.author.id in g.players:
                game = g
                break
                
        if not game:
            await ctx.send("❌ Você não está participando de nenhum jogo ativo!")
            return
            
        # Obtém o jogador
        player = game.players[ctx.author.id]
        
        # Verifica se o jogador está vivo
        if player.status != 'vivo':
            await ctx.send("❌ Jogadores mortos não podem usar habilidades! Descanse em paz!")
            return
            
        # Verifica se o jogador está corrompido
        if player.corrupted:
            await ctx.send("❌ Você está corrompido e não pode usar habilidades nesta fase!")
            player.corrupted = False  # Reseta para a próxima fase
            return
            
        # Verifica se é a fase correta para a ação
        if action in ["proteger", "marcar_observar", "reviver_uma_vez", "marcar_alvo_inicial", 
                     "revelar_alvo_viloes", "usar_pocao_vida", "usar_pocao_morte", 
                     "marcar_alvo_revelar", "ver_aura", "dar_voz_ao_morto", "formar_casal", 
                     "infectar_inicial", "exterminar_infectados", "corromper", "eliminar"]:
            # Ações noturnas
            if game.game_phase != 'night':
                await ctx.send("❌ Esta ação só pode ser usada durante a noite!")
                return
        elif action in ["atirar"]:
            # Ações diurnas
            if game.game_phase not in ['day_discussion', 'day_vote']:
                await ctx.send("❌ Esta ação só pode ser usada durante o dia!")
                return
        else:
            await ctx.send("❌ Ação desconhecida!")
            return
            
        # Verifica se o jogador tem o papel correto para a ação
        valid_action = False
        
        if action == "proteger" and player.role.name == "Guarda-costas":
            valid_action = await self._handle_bodyguard_protection(ctx, game, player, **kwargs)
        elif action == "marcar_observar" and player.role.name == "Detetive":
            valid_action = await self._handle_detective_observation(ctx, game, player, **kwargs)
        elif action == "reviver_uma_vez" and player.role.name == "Anjo":
            valid_action = await self._handle_angel_revival(ctx, game, player, **kwargs)
        elif action == "atirar" and player.role.name == "Xerife":
            valid_action = await self._handle_sheriff_shot(ctx, game, player, **kwargs)
        elif action == "eliminar" and player.role.faction == "vilões":
            valid_action = await self._handle_villain_elimination(ctx, game, player, **kwargs)
        elif action == "marcar_alvo_inicial" and player.role.name == "Assassino Júnior":
            valid_action = await self._handle_junior_target(ctx, game, player, **kwargs)
        elif action == "revelar_alvo_viloes" and player.role.name == "Cúmplice":
            valid_action = await self._handle_accomplice_reveal(ctx, game, player, **kwargs)
        elif action in ["usar_pocao_vida", "usar_pocao_morte"] and player.role.name == "Bruxo":
            valid_action = await self._handle_witch_potion(ctx, game, player, action, **kwargs)
        elif action == "marcar_alvo_revelar" and player.role.name == "Fofoqueiro":
            valid_action = await self._handle_gossiper_target(ctx, game, player, **kwargs)
        elif action == "ver_aura" and player.role.name == "Vidente de Aura":
            valid_action = await self._handle_aura_vision(ctx, game, player, **kwargs)
        elif action == "dar_voz_ao_morto" and player.role.name == "Médium":
            valid_action = await self._handle_medium_action(ctx, game, player, **kwargs)
        elif action == "formar_casal" and player.role.name == "Cupido":
            valid_action = await self._handle_cupid_action(ctx, game, player, **kwargs)
        elif action == "infectar_inicial" and player.role.name == "A Praga":
            valid_action = await self._handle_plague_infection(ctx, game, player, **kwargs)
        elif action == "exterminar_infectados" and player.role.name == "A Praga":
            valid_action = await self._handle_plague_extermination(ctx, game, player, **kwargs)
        elif action == "corromper" and player.role.name == "Corruptor":
            valid_action = await self._handle_corruptor_action(ctx, game, player, **kwargs)
        else:
            await ctx.send("❌ Você não tem o papel correto para usar esta habilidade!")
            return
            
        # Se a ação foi válida, registra-a
        if valid_action:
            # Registra a ação para processamento posterior
            if player.id not in game.night_actions:
                game.night_actions[player.id] = []
                
            game.night_actions[player.id].append(valid_action)
            
            # Envia mensagem de confirmação
            if action in self.action_success_messages:
                message = random.choice(self.action_success_messages[action])
                
                # Substitui os placeholders
                if "{target}" in message:
                    target = game.get_player(valid_action["target_id"])
                    message = message.replace("{target}", target.name if target else "???")
                if "{target1}" in message and "{target2}" in message:
                    target1 = game.get_player(valid_action["target1_id"])
                    target2 = game.get_player(valid_action["target2_id"])
                    message = message.replace("{target1}", target1.name if target1 else "???")
                    message = message.replace("{target2}", target2.name if target2 else "???")
                if "{aura_result}" in message:
                    message = message.replace("{aura_result}", valid_action.get("aura_result", "???"))
                if "{role}" in message:
                    target = game.get_player(valid_action["target_id"])
                    message = message.replace("{role}", target.role.name if target and target.role else "???")
                
                await ctx.send(message)

    async def _handle_bodyguard_protection(self, ctx, game, player, **kwargs):
        """Processa a ação de proteção do Guarda-costas."""
        target_id = kwargs.get("target_id")
        if not target_id:
            await ctx.send("❌ Você precisa especificar um alvo para proteger!")
            return False
            
        # Verifica se o alvo existe e está vivo
        target = game.get_player(target_id)
        if not target or target.status != 'vivo':
            message = random.choice(self.action_failure_messages["proteger"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        # Verifica se não está tentando se proteger
        if target_id == player.id:
            message = random.choice(self.action_failure_messages["proteger"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        # Verifica se já protegeu este alvo antes
        if hasattr(player, 'protected_targets') and target_id in player.protected_targets:
            message = random.choice(self.action_failure_messages["proteger"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        # Registra o alvo protegido
        if not hasattr(player, 'protected_targets'):
            player.protected_targets = set()
        player.protected_targets.add(target_id)
        
        return {
            "action": "proteger",
            "target_id": target_id
        }

    async def _handle_detective_observation(self, ctx, game, player, **kwargs):
        """Processa a ação de observação do Detetive."""
        target1_id = kwargs.get("target1_id")
        target2_id = kwargs.get("target2_id")
        
        if not target1_id or not target2_id:
            await ctx.send("❌ Você precisa especificar dois alvos para observar!")
            return False
            
        # Verifica se os alvos existem e estão vivos
        target1 = game.get_player(target1_id)
        target2 = game.get_player(target2_id)
        
        if not target1 or not target2 or target1.status != 'vivo' or target2.status != 'vivo' or target1_id == target2_id:
            message = random.choice(self.action_failure_messages["marcar_observar"])
            await ctx.send(message)
            return False
            
        return {
            "action": "marcar_observar",
            "target1_id": target1_id,
            "target2_id": target2_id
        }

    async def _handle_angel_revival(self, ctx, game, player, **kwargs):
        """Processa a ação de reviver do Anjo."""
        target_id = kwargs.get("target_id")
        
        if not target_id:
            await ctx.send("❌ Você precisa especificar um alvo para reviver!")
            return False
            
        # Verifica se o alvo existe e está morto
        target = game.get_player(target_id)
        if not target or target.status != 'morto':
            message = random.choice(self.action_failure_messages["reviver_uma_vez"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        # Verifica se já usou o poder
        if hasattr(player, 'revival_used') and player.revival_used:
            message = random.choice(self.action_failure_messages["reviver_uma_vez"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        # Marca o poder como usado
        player.revival_used = True
        
        # Revive o jogador
        target.status = 'vivo'
        
        # Reproduz som de reviver
        voice_manager = self.bot.get_cog("VoiceManager")
        if voice_manager:
            await voice_manager.play_sound(game, 'reviver')
        
        return {
            "action": "reviver_uma_vez",
            "target_id": target_id
        }

    async def _handle_sheriff_shot(self, ctx, game, player, **kwargs):
        """Processa a ação de tiro do Xerife."""
        target_id = kwargs.get("target_id")
        
        if not target_id:
            await ctx.send("❌ Você precisa especificar um alvo para atirar!")
            return False
            
        # Verifica se o alvo existe e está vivo
        target = game.get_player(target_id)
        if not target or target.status != 'vivo':
            message = random.choice(self.action_failure_messages["atirar"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        # Verifica se ainda tem balas
        if not hasattr(player, 'sheriff_bullets'):
            player.sheriff_bullets = 2
            
        if player.sheriff_bullets <= 0:
            message = random.choice(self.action_failure_messages["atirar"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        # Gasta uma bala
        player.sheriff_bullets -= 1
        
        # Marca que o Xerife atirou hoje
        game.sheriff_shot_today = True
        
        # Reproduz som de tiro
        voice_manager = self.bot.get_cog("VoiceManager")
        if voice_manager:
            await voice_manager.play_sound(game, 'tiro')
        
        # Verifica se acertou o Assassino Alfa (vitória da Cidade)
        if target.role.name == "Assassino Alfa":
            # Mata o Assassino Alfa
            target.status = 'morto'
            
            # Anuncia a vitória da Cidade
            await game.game_channel.send(f"🔫 **BANG!** O Xerife {player.user.mention} atirou em {target.user.mention} e revelou o **Assassino Alfa**! A Cidade vence!")
            
            # Reproduz som de vitória da cidade
            if voice_manager:
                await voice_manager.play_sound(game, 'vitoria_cidade')
            
            # Encerra o jogo com vitória da Cidade
            game_manager = self.bot.get_cog("GameManager")
            if game_manager:
                await game.game_channel.send("**🏁 FIM DE JOGO! ACABOU A BRINCADEIRA! 🏁**\n\n🏆 A CIDADE VENCEU! O Xerife eliminou o Assassino Alfa! Justiça foi feita!\n*Motivo: O Xerife eliminou o Assassino Alfa!*")
                await game_manager.end_game(game)
        
        # Verifica se acertou o Prefeito (vitória dos Vilões)
        elif target.role.name == "Prefeito":
            # Mata o Prefeito
            target.status = 'morto'
            
            # Anuncia a vitória dos Vilões
            await game.game_channel.send(f"🔫 **BANG!** O Xerife {player.user.mention} atirou em {target.user.mention} e matou o **Prefeito**! Os Vilões vencem!")
            
            # Reproduz som de vitória dos vilões
            if voice_manager:
                await voice_manager.play_sound(game, 'vitoria_viloes')
            
            # Encerra o jogo com vitória dos Vilões
            game_manager = self.bot.get_cog("GameManager")
            if game_manager:
                await game.game_channel.send("**🏁 FIM DE JOGO! ACABOU A BRINCADEIRA! 🏁**\n\n🏆 OS VILÕES VENCERAM! O Xerife matou o Prefeito por engano! Que desastre!\n*Motivo: O Xerife eliminou o Prefeito!*")
                await game_manager.end_game(game)
        
        # Caso contrário, apenas mata o alvo
        else:
            # Mata o alvo
            target.status = 'morto'
            
            # Anuncia o tiro
            await game.game_channel.send(f"🔫 **BANG!** O Xerife {player.user.mention} atirou em {target.user.mention} e revelou ser **{target.role.name}**!")
            
            # Verifica se o alvo era um Amante
            if target.lover:
                lover = target.lover
                if lover.status == 'vivo':
                    lover.status = 'morto'
                    await game.game_channel.send(f"Oh, a tragédia! 💔 {target.user.mention} morreu, e seu amor secreto, {lover.user.mention}, não aguentou a dor e morreu de coração partido! Que dramático!")
        
        return {
            "action": "atirar",
            "target_id": target_id
        }

    async def _handle_villain_elimination(self, ctx, game, player, **kwargs):
        """Processa a ação de eliminação dos Vilões."""
        target_id = kwargs.get("target_id")
        
        if not target_id:
            await ctx.send("❌ Você precisa especificar um alvo para eliminar!")
            return False
            
        # Verifica se o alvo existe e está vivo
        target = game.get_player(target_id)
        if not target or target.status != 'vivo':
            message = random.choice(self.action_failure_messages["eliminar"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        return {
            "action": "eliminar",
            "target_id": target_id
        }

    async def _handle_junior_target(self, ctx, game, player, **kwargs):
        """Processa a ação de marcar alvo do Assassino Júnior."""
        target_id = kwargs.get("target_id")
        
        if not target_id:
            await ctx.send("❌ Você precisa especificar um alvo para marcar!")
            return False
            
        # Verifica se o alvo existe e está vivo
        target = game.get_player(target_id)
        if not target or target.status != 'vivo':
            message = random.choice(self.action_failure_messages["marcar_alvo_inicial"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        # Verifica se já marcou alguém
        if hasattr(player, 'marked_target') and player.marked_target:
            message = random.choice(self.action_failure_messages["marcar_alvo_inicial"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        return {
            "action": "marcar_alvo_inicial",
            "target_id": target_id
        }

    async def _handle_accomplice_reveal(self, ctx, game, player, **kwargs):
        """Processa a ação de revelar alvo do Cúmplice."""
        target_id = kwargs.get("target_id")
        
        if not target_id:
            await ctx.send("❌ Você precisa especificar um alvo para revelar!")
            return False
            
        # Verifica se o alvo existe e está vivo
        target = game.get_player(target_id)
        if not target or target.status != 'vivo':
            message = random.choice(self.action_failure_messages["revelar_alvo_viloes"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        # Verifica se já revelou alguém
        if hasattr(player, 'revealed_target') and player.revealed_target:
            message = random.choice(self.action_failure_messages["revelar_alvo_viloes"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        # Marca como revelado
        player.revealed_target = True
        
        return {
            "action": "revelar_alvo_viloes",
            "target_id": target_id
        }

    async def _handle_witch_potion(self, ctx, game, player, action, **kwargs):
        """Processa as ações de poções do Bruxo."""
        target_id = kwargs.get("target_id")
        
        if not target_id:
            await ctx.send("❌ Você precisa especificar um alvo para a poção!")
            return False
            
        # Verifica se o alvo existe e está vivo
        target = game.get_player(target_id)
        if not target or target.status != 'vivo':
            message = random.choice(self.action_failure_messages[action])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        # Verifica se já usou a poção
        if action == "usar_pocao_vida":
            if hasattr(player, 'life_potion_used') and player.life_potion_used:
                message = random.choice(self.action_failure_messages[action])
                message = message.replace("{target}", target.name if target else "???")
                await ctx.send(message)
                return False
        elif action == "usar_pocao_morte":
            if hasattr(player, 'death_potion_used') and player.death_potion_used:
                message = random.choice(self.action_failure_messages[action])
                message = message.replace("{target}", target.name if target else "???")
                await ctx.send(message)
                return False
        
        return {
            "action": action,
            "target_id": target_id
        }

    async def _handle_gossiper_target(self, ctx, game, player, **kwargs):
        """Processa a ação de marcar alvo do Fofoqueiro."""
        target_id = kwargs.get("target_id")
        
        if not target_id:
            await ctx.send("❌ Você precisa especificar um alvo para marcar!")
            return False
            
        # Verifica se o alvo existe e está vivo
        target = game.get_player(target_id)
        if not target or target.status != 'vivo':
            message = random.choice(self.action_failure_messages["marcar_alvo_revelar"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        # Verifica se já marcou alguém
        if hasattr(player, 'marked_target') and player.marked_target:
            message = random.choice(self.action_failure_messages["marcar_alvo_revelar"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        return {
            "action": "marcar_alvo_revelar",
            "target_id": target_id
        }

    async def _handle_aura_vision(self, ctx, game, player, **kwargs):
        """Processa a ação de ver aura do Vidente de Aura."""
        target_id = kwargs.get("target_id")
        
        if not target_id:
            await ctx.send("❌ Você precisa especificar um alvo para ver a aura!")
            return False
            
        # Verifica se o alvo existe e está vivo
        target = game.get_player(target_id)
        if not target or target.status != 'vivo':
            message = random.choice(self.action_failure_messages["ver_aura"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        # Determina a aura
        aura = "da Cidade" if target.role.faction == "cidade" else "Sombria"
        
        return {
            "action": "ver_aura",
            "target_id": target_id,
            "aura_result": aura
        }

    async def _handle_medium_action(self, ctx, game, player, **kwargs):
        """Processa a ação de dar voz ao morto do Médium."""
        target_id = kwargs.get("target_id")
        
        if not target_id:
            await ctx.send("❌ Você precisa especificar um jogador morto para dar voz!")
            return False
            
        # Verifica se o alvo existe e está morto
        target = game.get_player(target_id)
        if not target or target.status != 'morto':
            message = random.choice(self.action_failure_messages["dar_voz_ao_morto"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        return {
            "action": "dar_voz_ao_morto",
            "target_id": target_id
        }

    async def _handle_cupid_action(self, ctx, game, player, **kwargs):
        """Processa a ação de formar casal do Cupido."""
        target1_id = kwargs.get("target1_id")
        target2_id = kwargs.get("target2_id")
        
        if not target1_id or not target2_id:
            await ctx.send("❌ Você precisa especificar dois jogadores para formar um casal!")
            return False
            
        # Verifica se os alvos existem e estão vivos
        target1 = game.get_player(target1_id)
        target2 = game.get_player(target2_id)
        
        if not target1 or not target2 or target1.status != 'vivo' or target2.status != 'vivo' or target1_id == target2_id:
            message = random.choice(self.action_failure_messages["formar_casal"])
            await ctx.send(message)
            return False
            
        # Verifica se já formou um casal
        if game.lovers:
            message = random.choice(self.action_failure_messages["formar_casal"])
            await ctx.send(message)
            return False
            
        return {
            "action": "formar_casal",
            "target1_id": target1_id,
            "target2_id": target2_id
        }

    async def _handle_plague_infection(self, ctx, game, player, **kwargs):
        """Processa a ação de infectar da Praga."""
        target_id = kwargs.get("target_id")
        
        if not target_id:
            await ctx.send("❌ Você precisa especificar um alvo para infectar!")
            return False
            
        # Verifica se o alvo existe e está vivo
        target = game.get_player(target_id)
        if not target or target.status != 'vivo':
            message = random.choice(self.action_failure_messages["infectar_inicial"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        # Verifica se já infectou alguém
        if game.infected_players:
            message = random.choice(self.action_failure_messages["infectar_inicial"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        return {
            "action": "infectar_inicial",
            "target_id": target_id
        }

    async def _handle_plague_extermination(self, ctx, game, player, **kwargs):
        """Processa a ação de exterminar infectados da Praga."""
        # Verifica se há infectados
        if not game.infected_players:
            message = random.choice(self.action_failure_messages["exterminar_infectados"])
            await ctx.send(message)
            return False
            
        # Verifica se já usou o extermínio
        if hasattr(player, 'extermination_used') and player.extermination_used:
            message = random.choice(self.action_failure_messages["exterminar_infectados"])
            await ctx.send(message)
            return False
            
        return {
            "action": "exterminar_infectados"
        }

    async def _handle_corruptor_action(self, ctx, game, player, **kwargs):
        """Processa a ação de corromper do Corruptor."""
        target_id = kwargs.get("target_id")
        
        if not target_id:
            await ctx.send("❌ Você precisa especificar um alvo para corromper!")
            return False
            
        # Verifica se o alvo existe e está vivo
        target = game.get_player(target_id)
        if not target or target.status != 'vivo':
            message = random.choice(self.action_failure_messages["corromper"])
            message = message.replace("{target}", target.name if target else "???")
            await ctx.send(message)
            return False
            
        return {
            "action": "corromper",
            "target_id": target_id
        }

# Função para adicionar o Cog ao bot
def setup(bot):
    bot.add_cog(RoleHandler(bot))
