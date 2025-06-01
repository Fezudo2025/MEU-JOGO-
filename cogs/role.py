# models/role.py
from typing import List, Optional, Dict, Any

class Role:
    """Representa um papel no jogo Cidade Dorme."""
    
    def __init__(self, name: str, faction: str, description: str, 
                 night_action: bool = False, day_action: bool = False,
                 first_night_only: bool = False, image_url: str = None):
        self.name = name
        self.faction = faction  # "cidade", "vilões" ou "solo"
        self.description = description
        self.night_action = night_action  # Tem ação noturna?
        self.day_action = day_action  # Tem ação diurna?
        self.first_night_only = first_night_only  # Ação apenas na primeira noite?
        self.image_url = image_url  # URL da imagem do papel
        
    def to_dict(self) -> Dict[str, Any]:
        """Converte o papel para um dicionário."""
        return {
            "name": self.name,
            "faction": self.faction,
            "description": self.description,
            "night_action": self.night_action,
            "day_action": self.day_action,
            "first_night_only": self.first_night_only,
            "image_url": self.image_url
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Role':
        """Cria um papel a partir de um dicionário."""
        return cls(
            name=data["name"],
            faction=data["faction"],
            description=data["description"],
            night_action=data.get("night_action", False),
            day_action=data.get("day_action", False),
            first_night_only=data.get("first_night_only", False),
            image_url=data.get("image_url")
        )

def get_all_roles() -> List[Role]:
    """Retorna todos os papéis disponíveis no jogo."""
    
    # Caminho base para as imagens dos papéis
    base_url = "https://cdn.discordapp.com/attachments/CHANNEL_ID/"  # Será substituído pelo ID do canal real
    
    # Alternativa para testes locais
    local_path = "assets/"
    
    roles = [
        Role(
            name="Prefeito",
            faction="cidade",
            description="É o líder da cidade e alvo dos assassinos. Anula automaticamente a primeira votação diurna que o lincharia. No início do jogo, recebe 3 nomes: um é o Anjo, outro é o Xerife e outro é o Cúmplice, mas não sabe quem é quem.",
            night_action=False,
            day_action=True,
            image_url=f"{local_path}prefeito_card.png"
        ),
        Role(
            name="Guarda-costas",
            faction="cidade",
            description="Toda noite pode proteger alguém. Resiste ao primeiro ataque mas morre no segundo. Não pode se proteger nem repetir a proteção no mesmo jogador.",
            night_action=True,
            image_url=f"{local_path}guarda_costas_card.png"
        ),
        Role(
            name="Detetive",
            faction="cidade",
            description="Toda noite pode marcar dois jogadores para observar. Se um dos jogadores for morto, receberá dois nomes de possíveis suspeitos.",
            night_action=True,
            image_url=f"{local_path}detetive_card.png"
        ),
        Role(
            name="Anjo",
            faction="cidade",
            description="Pode reviver um jogador uma única vez no jogo. No início do jogo recebe o nome de duas pessoas, uma é o Prefeito e o outro o Cúmplice, mas não sabe quem é quem.",
            night_action=True,
            image_url=f"{local_path}anjo_card.png"
        ),
        Role(
            name="Xerife",
            faction="cidade",
            description="Tem duas balas. Pode efetuar um disparo por dia, ao realizar o primeiro disparo sua função é revelada. Se o disparo atingir o Assassino Alfa, cidade vence automaticamente. Se o disparo atingir o Prefeito, vilões vencem automaticamente.",
            day_action=True,
            image_url=f"{local_path}xerife_card.png"
        ),
        Role(
            name="Assassino Alfa",
            faction="vilões",
            description="Seu voto conta por dois. Toda noite vota para eliminar alguém. Na primeira noite conhece seus parceiros vilões.",
            night_action=True,
            image_url=f"{local_path}assassino_alfa_card.png"
        ),
        Role(
            name="Assassino Júnior",
            faction="vilões",
            description="Na primeira noite marca um alvo. Se o Assassino Júnior morrer, o alvo marcado também morre. Toda noite vota para eliminar alguém.",
            night_action=True,
            first_night_only=True,
            image_url=f"{local_path}assassino_junior_card.png"
        ),
        Role(
            name="Cúmplice",
            faction="vilões",
            description="Na primeira noite pode escolher um jogador para revelar seu papel aos vilões. Toda noite vota para eliminar alguém.",
            night_action=True,
            first_night_only=True,
            image_url=f"{local_path}cumplice_card.png"
        ),
        Role(
            name="Palhaço",
            faction="solo",
            description="Vence o jogo se for linchado durante o dia. Não sabe quem são os outros jogadores.",
            day_action=False,
            night_action=False,
            image_url=f"{local_path}palhaco_card.png"
        ),
        Role(
            name="Bruxo",
            faction="vilões",
            description="Possui uma poção da vida e uma poção da morte. Pode usar uma por noite. A poção da vida salva alguém que seria morto naquela noite. A poção da morte mata alguém. Cada poção só pode ser usada uma vez. Toda noite vota para eliminar alguém.",
            night_action=True,
            image_url=f"{local_path}bruxo_card.png"
        ),
        Role(
            name="Fofoqueiro",
            faction="cidade",
            description="Na primeira noite marca um alvo. Se o Fofoqueiro morrer, o papel do alvo marcado é revelado para todos. Não tem outras habilidades especiais.",
            night_action=True,
            first_night_only=True,
            image_url=f"{local_path}fofoqueiro_card.png"
        ),
        Role(
            name="Vidente de Aura",
            faction="cidade",
            description="Toda noite pode verificar a aura de um jogador, descobrindo se ele é da Cidade ou não (Vilões e Solos não são da Cidade).",
            night_action=True,
            image_url=f"{local_path}vidente_aura_card.png"
        ),
        Role(
            name="Médium",
            faction="cidade",
            description="A partir da segunda noite, pode escolher um jogador morto para falar durante o próximo dia. Após esse dia, o jogador morto volta a ficar silenciado.",
            night_action=True,
            image_url=f"{local_path}medium_card.png"
        ),
        Role(
            name="Cupido",
            faction="cidade",
            description="Na primeira noite, escolhe dois jogadores para serem Amantes. Os Amantes sabem quem é seu par, mas não sabem o papel um do outro. Se um Amante morrer, o outro morre de coração partido. Os Amantes vencem se sobreviverem até o final, independente de outras condições de vitória.",
            night_action=True,
            first_night_only=True,
            image_url=f"{local_path}cupido_card.png"
        ),
        Role(
            name="A Praga",
            faction="solo",
            description="Na primeira noite, infecta um jogador (paciente zero). Jogadores que interagem com infectados também ficam infectados. Uma vez por jogo, pode matar todos os infectados. Vence se todos os jogadores vivos estiverem infectados.",
            night_action=True,
            first_night_only=True,
            image_url=f"{local_path}praga_card.png"
        ),
        Role(
            name="Corruptor",
            faction="solo",
            description="Toda noite pode corromper um jogador, impedindo-o de usar suas habilidades na próxima fase. Vence se estiver vivo no final do jogo e o Prefeito estiver morto.",
            night_action=True,
            image_url=f"{local_path}corruptor_card.png"
        )
    ]
    
    return roles

def get_role_by_name(name: str) -> Optional[Role]:
    """Retorna um papel pelo nome, ou None se não existir."""
    for role in get_all_roles():
        if role.name.lower() == name.lower():
            return role
    return None
