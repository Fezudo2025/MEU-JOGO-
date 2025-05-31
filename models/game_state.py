# models/game_state.py
import nextcord
from typing import Dict, List, Optional, Tuple
import time
import asyncio

# Import other models
from .player import Player
from .role import Role, get_role, ALL_ROLES
import random

class GameState:
    """Mantém o estado atual de uma partida de Cidade Dorme."""
    def __init__(self, interaction: nextcord.Interaction):
        self.guild: nextcord.Guild = interaction.guild
        self.game_channel: nextcord.TextChannel = interaction.channel
        self.voice_channel: Optional[nextcord.VoiceChannel] = None
        self.players: Dict[int, Player] = {} # {user_id: Player object}
        self.game_phase: str = "lobby" # lobby, starting, night, day_report, day_discussion, day_vote, processing_vote, ended
        self.day_number: int = 0
        self.night_number: int = 0
        self.start_time: float = time.time()
        self.phase_timer_task: Optional[asyncio.Task] = None

        # Estado específico do jogo
        self.roles_in_game: List[Role] = []
        self.night_actions: List[Dict] = [] # Lista de ações pendentes da noite {player_id, ability, target_ids, ...}
        self.killed_tonight: List[Tuple[Player, str]] = [] # Lista de (Player, Razão da morte)
        self.votes_today: Dict[int, int] = {} # {voter_id: target_id}
        self.lynched_today: Optional[Player] = None
        self.mayor_lynch_immunity_used: bool = False
        self.lovers: Optional[Tuple[Player, Player]] = None
        self.infected_players: List[Player] = []
        self.dead_speaker_id: Optional[int] = None # ID do jogador morto que pode falar hoje (Médium)

        # Configurações (podem virar argumentos no futuro)
        self.min_players = 8
        self.max_players = 16
        self.max_nights = 6 # O jogo termina no início do Dia 7

    def add_player(self, member: nextcord.Member):
        """Adiciona um jogador ao estado do jogo."""
        if member.id not in self.players:
            self.players[member.id] = Player(member)
            print(f"Jogador {member.name} adicionado ao jogo no servidor {self.guild.name}.")

    def get_player(self, user_id: int) -> Optional[Player]:
        """Retorna um objeto Player pelo ID do usuário."""
        return self.players.get(user_id)

    def get_living_players(self) -> List[Player]:
        """Retorna uma lista de jogadores vivos."""
        return [p for p in self.players.values() if p.status == "vivo"]

    def get_dead_players(self) -> List[Player]:
        """Retorna uma lista de jogadores mortos."""
        return [p for p in self.players.values() if p.status == "morto"]

    def get_players_by_faction(self, faction: str, alive_only: bool = True) -> List[Player]:
        """Retorna jogadores de uma facção específica."""
        player_list = []
        for p in self.players.values():
            if p.role and p.role.faction == faction:
                if not alive_only or p.status == "vivo":
                    player_list.append(p)
        return player_list

    def get_player_by_role_name(self, role_name: str, alive_only: bool = True) -> Optional[Player]:
        """Retorna o primeiro jogador encontrado com um nome de papel específico."""
        for p in self.players.values():
            if p.role and p.role.name == role_name:
                if not alive_only or p.status == "vivo":
                    return p
        return None

    def assign_roles(self):
        """Distribui os papéis aleatoriamente aos jogadores baseado na prioridade."""
        num_players = len(self.players)
        if num_players < self.min_players or num_players > self.max_players:
            raise ValueError("Número de jogadores inválido para iniciar a partida.")

        # Define a lista de papéis prioritários
        priority_roles = [
            "Prefeito", "Assassino Alfa", "Guarda-costas", "Anjo", "Detetive",
            "Assassino Júnior", "Cúmplice", "Xerife", "Palhaço", "Bruxo",
            "Fofoqueiro", "Vidente de Aura", "Médium", "Cupido", "A Praga", "Corruptor"
        ]

        # Seleciona os papéis para o número atual de jogadores
        roles_to_assign_names = priority_roles[:num_players]
        random.shuffle(roles_to_assign_names) # Embaralha os papéis selecionados

        self.roles_in_game = [get_role(name) for name in roles_to_assign_names if get_role(name)]
        if len(self.roles_in_game) != num_players:
             raise ValueError("Erro ao buscar definições dos papéis selecionados.")

        player_list = list(self.players.values())
        random.shuffle(player_list) # Embaralha os jogadores

        for i, player in enumerate(player_list):
            player.assign_role(self.roles_in_game[i])
            print(f"Papel {player.role.name} atribuído a {player.name}.")

        # Lógica pós-atribuição (informações iniciais)
        self._setup_initial_info()

    def _setup_initial_info(self):
        """Configura informações que alguns papéis recebem no início."""
        mayor = self.get_player_by_role_name("Prefeito", alive_only=False)
        angel = self.get_player_by_role_name("Anjo", alive_only=False)
        sheriff = self.get_player_by_role_name("Xerife", alive_only=False)
        accomplice = self.get_player_by_role_name("Cúmplice", alive_only=False)

        possible_mayor_targets = []
        if angel: possible_mayor_targets.append(angel.name)
        if sheriff: possible_mayor_targets.append(sheriff.name)
        if accomplice: possible_mayor_targets.append(accomplice.name)

        if mayor and len(possible_mayor_targets) >= 3:
            mayor.mayor_initial_names = random.sample(possible_mayor_targets, 3)
            print(f"Prefeito {mayor.name} recebe nomes: {mayor.mayor_initial_names}")

        possible_angel_targets = []
        if mayor: possible_angel_targets.append(mayor.name)
        if accomplice: possible_angel_targets.append(accomplice.name)

        if angel and len(possible_angel_targets) >= 2:
            angel.angel_initial_names = random.sample(possible_angel_targets, 2)
            print(f"Anjo {angel.name} recebe nomes: {angel.angel_initial_names}")

    def add_night_action(self, player_id: int, ability: str, target_ids: List[int], **kwargs):
        """Adiciona uma ação noturna à fila para processamento."""
        # Remove ação anterior do mesmo jogador para a mesma habilidade (evita spam/troca)
        self.night_actions = [a for a in self.night_actions if not (a["player_id"] == player_id and a["ability"] == ability)]
        action = {"player_id": player_id, "ability": ability, "target_ids": target_ids}
        action.update(kwargs) # Adiciona quaisquer outros parâmetros (ex: potion_type)
        self.night_actions.append(action)
        print(f"Ação noturna adicionada: {action}")

    def add_vote(self, voter_id: int, target_id: int):
        """Registra um voto diurno."""
        self.votes_today[voter_id] = target_id
        print(f"Voto registrado: {voter_id} -> {target_id}")

    def reset_nightly_state(self):
        """Reseta variáveis que são por noite."""
        self.night_actions = []
        self.killed_tonight = []
        # self.dead_speaker_id = None # Resetar aqui ou no início do dia?
        for p in self.players.values():
            p.reset_nightly_flags()
        print(f"Estado noturno resetado para a noite {self.night_number + 1}.")

    def reset_daily_state(self):
        """Reseta variáveis que são por dia."""
        self.votes_today = {}
        self.lynched_today = None
        self.dead_speaker_id = None # Resetar ID do falante do médium no início do dia
        print(f"Estado diurno resetado para o dia {self.day_number + 1}.")

    async def cancel_phase_timer(self):
        """Cancela o timer da fase atual, se existir."""
        if self.phase_timer_task and not self.phase_timer_task.done():
            self.phase_timer_task.cancel()
            print("Timer da fase cancelado.")
            try:
                await self.phase_timer_task # Aguarda o cancelamento concluir
            except asyncio.CancelledError:
                print("Confirmação de cancelamento do timer recebida.")
            self.phase_timer_task = None

    def check_win_conditions(self) -> Optional[Tuple[str, str]]:
        """Verifica se alguma condição de vitória foi atingida.
           Retorna uma tupla (Vencedor, Razão) ou None.
        """
        living_players = self.get_living_players()
        num_living = len(living_players)
        living_factions = {p.role.faction for p in living_players if p.role}

        # Condições de Vitória Imediata (já tratadas em outros locais, mas bom verificar)
        # - Palhaço linchado (tratado em process_lynch)
        # - Praga exterminou facção (tratado em RoleHandler)
        # - Xerife matou Alfa/Prefeito (tratado em CommandInterface/RoleHandler diurno)

        # Condições de Fim de Jogo por Eliminação
        city_alive = any(p.role.faction == "Cidade" for p in living_players if p.role)
        villains_alive = any(p.role.faction == "Vilões" for p in living_players if p.role)
        solos_alive = any(p.role.faction == "Solo" for p in living_players if p.role)

        # 1. Vitória da Cidade: Todos os Vilões e Solos (exceto talvez Amantes/Corruptor em cenários finais) foram eliminados.
        if city_alive and not villains_alive and not solos_alive:
            # Caso especial: Amantes da cidade? Se sim, eles vencem.
            if self.lovers:
                lover1, lover2 = self.lovers
                if lover1.status == 'vivo' and lover2.status == 'vivo':
                    return ("Amantes", "O amor venceu! Sobreviveram juntos até o fim.")
            return ("Cidade", "Todos os Vilões e Solos foram eliminados!")

        # 2. Vitória dos Vilões: Número de Vilões >= Número de não-Vilões OU todos da Cidade/Solos eliminados.
        num_villains = len(self.get_players_by_faction("Vilões"))
        num_non_villains = num_living - num_villains
        if villains_alive and (num_villains >= num_non_villains or (not city_alive and not solos_alive)):
             # Caso especial: Amantes vilões/misto? Se sim, eles vencem.
            if self.lovers:
                lover1, lover2 = self.lovers
                if lover1.status == 'vivo' and lover2.status == 'vivo':
                    return ("Amantes", "O amor venceu! Sobreviveram juntos até o fim.")
            return ("Vilões", "A Cidade foi dominada ou eliminada!")

        # 3. Vitória dos Amantes: Sobreviveram juntos até o fim (verificado acima e no final).
        if self.lovers:
            lover1, lover2 = self.lovers
            if lover1.status == 'vivo' and lover2.status == 'vivo':
                # Se só sobraram os amantes, eles vencem
                if num_living == 2:
                    return ("Amantes", "Só restaram os pombinhos! O amor venceu!")
                # Se não há mais ameaças (Vilões/Solos perigosos) e a cidade não pode mais vencer?
                # Esta condição é complexa, geralmente tratada no final do jogo.

        # 4. Vitória do Corruptor: Sobreviveu até o final (geralmente Dia 7 ou condição de 1v1).
        # Esta é verificada principalmente em determine_final_winner.

        # 5. Vitória da Praga: Já tratada no RoleHandler ao usar extermínio.

        return None # Nenhuma condição de vitória atingida ainda

    def determine_final_winner(self) -> Tuple[str, str]:
        """Determina o vencedor no final do tempo (Dia 7) ou impasse."""
        living_players = self.get_living_players()
        num_living = len(living_players)

        # Cenário do Dia 7 (após votação e possível tiro do Xerife)
        # Regra 5: Prefeito e Vilão vivos -> Xerife atira (se vivo/com bala)
        # -> Se Prefeito e Vilão ainda vivos -> Amantes vencem (se vivos)
        # -> Senão -> Corruptor vence (se vivo)
        # -> Senão -> Prefeito vence

        # Simplificação para agora: Prioridades no final
        # 1. Amantes (se ambos vivos)
        if self.lovers:
            lover1, lover2 = self.lovers
            if lover1.status == 'vivo' and lover2.status == 'vivo':
                return ("Amantes", "Sobreviveram juntos até o fim do tempo! O amor prevaleceu!")

        # 2. Corruptor (se vivo)
        corruptor = self.get_player_by_role_name("Corruptor")
        if corruptor and corruptor.status == 'vivo':
            return ("Corruptor", "Sobreviveu até o fim do tempo na moita! Vitória solo!")

        # 3. Cidade (se Prefeito vivo e Vilões eliminados? Ou se mais Cidades que Vilões?)
        # Vamos usar a condição padrão de check_win_conditions
        city_wins = self.check_win_conditions()
        if city_wins and city_wins[0] == "Cidade":
            return city_wins
        if city_wins and city_wins[0] == "Vilões":
             return city_wins

        # 4. Empate? (Se nenhuma das condições acima for atendida)
        return ("Empate", "O tempo acabou e ninguém conseguiu uma vitória clara!")

