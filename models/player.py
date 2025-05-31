# models/player.py
import nextcord
from typing import Optional, Dict, Any
from .role import Role # Importa a classe Role do mesmo diretório

class Player:
    """Representa um jogador na partida de Cidade Dorme."""
    def __init__(self, user: nextcord.Member, role: Optional[Role] = None):
        self.user: nextcord.Member = user # Objeto Member do Discord
        self.role: Optional[Role] = role # Objeto Role atribuído
        self.status: str = 'vivo' # Estados possíveis: 'vivo', 'morto'
        self.is_muted_by_bot: bool = False # Se o bot silenciou este jogador no voice channel
        self.votes_received_today: int = 0 # Votos recebidos na votação diurna atual
        self.voted_for_today: Optional[Player] = None # Em quem este jogador votou hoje
        self.can_act_tonight: bool = True # Se o jogador pode usar habilidades nesta noite (afetado por Corruptor)
        self.is_protected_tonight: bool = False # Se o jogador está protegido pelo Guarda-costas nesta noite
        self.is_targeted_by_detective: bool = False # Se foi alvo do Detetive nesta noite
        self.is_infected: bool = False # Se foi infectado pela Praga
        self.lover: Optional[Player] = None # Se este jogador é um Amante, quem é o outro
        self.marked_by_junior: Optional[Player] = None # Alvo marcado pelo Assassino Júnior (apenas no Júnior)
        self.revealed_by_accomplice: Optional[Player] = None # Alvo revelado pelo Cúmplice (apenas no Cúmplice)
        self.target_for_fofoqueiro: Optional[Player] = None # Alvo do Fofoqueiro (apenas no Fofoqueiro)
        self.initial_infection_target: Optional[Player] = None # Alvo inicial da Praga (apenas na Praga)

        # Habilidades com usos limitados
        self.angel_revive_used: bool = False # Anjo já usou o reviver?
        self.sheriff_shots_left: int = 2 if role and role.name == "Xerife" else 0 # Balas do Xerife
        self.sheriff_revealed: bool = False # Xerife já foi revelado?
        self.medium_speak_used: bool = False # Médium já usou a habilidade?
        self.plague_exterminate_used: bool = False # Praga já usou o exterminar?
        self.clown_can_win: bool = True # Palhaço ainda pode vencer (não foi linchado e sobreviveu)
        self.bodyguard_last_protected: Optional[Player] = None # Quem o Guarda-costas protegeu na noite anterior
        self.bodyguard_attack_count: int = 0 # Quantos ataques o Guarda-costas sofreu

        # Poções do Bruxo
        self.witch_life_potion_used: bool = False
        self.witch_death_potion_used: bool = False

        # Informações recebidas
        self.mayor_initial_names: list[str] = [] # Nomes recebidos pelo Prefeito
        self.angel_initial_names: list[str] = [] # Nomes recebidos pelo Anjo
        self.detective_suspects: list[str] = [] # Suspeitos recebidos pelo Detetive
        self.accomplice_revealed_role: Optional[Role] = None # Papel revelado ao Cúmplice

    @property
    def name(self) -> str:
        """Retorna o nome de exibição do jogador no servidor."""
        return self.user.display_name

    @property
    def id(self) -> int:
        """Retorna o ID do Discord do jogador."""
        return self.user.id

    def assign_role(self, role: Role):
        """Atribui um papel ao jogador."""
        self.role = role
        if role.name == "Xerife":
            self.sheriff_shots_left = 2

    def kill(self):
        """Marca o jogador como morto."""
        self.status = 'morto'
        print(f"Jogador {self.name} foi marcado como morto.")

    def revive(self):
        """Marca o jogador como vivo."""
        self.status = 'vivo'
        print(f"Jogador {self.name} foi revivido.")

    def reset_nightly_flags(self):
        """Reseta flags que são válidas apenas por uma noite."""
        self.can_act_tonight = True
        self.is_protected_tonight = False
        self.is_targeted_by_detective = False
        self.detective_suspects = []

    def reset_daily_flags(self):
        """Reseta flags que são válidas apenas por um dia."""
        self.votes_received_today = 0
        self.voted_for_today = None

    def __str__(self) -> str:
        role_name = self.role.name if self.role else "Nenhum"
        return f"{self.name} (ID: {self.id}, Papel: {role_name}, Status: {self.status})"

    def __repr__(self) -> str:
        return f"Player(user={self.user!r}, role={self.role!r})"

