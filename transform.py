"""
ETL - Etapa 2: TRANSFORM
Lê o JSON bruto salvo pelo extract.py, extrai só os campos úteis,
limpa/normaliza os dados e classifica os personagens por popularidade.

Versão COMENTADA LINHA A LINHA para estudo.
"""

# --- IMPORTS ---

import json       # pra ler o arquivo JSON bruto e escrever o resultado tratado
import logging    # pra registrar o que está acontecendo em cada etapa
from pathlib import Path  # pra lidar com caminhos de arquivo de forma segura


# --- CONFIGURAÇÃO DO LOG (igual ao extract.py) ---

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# --- CONFIGURAÇÕES DO PIPELINE ---

ANIME_ID = 40748  

INPUT_FILE = Path("data/raw") / f"personagens_{ANIME_ID}.json"
# ^ caminho de onde vamos LER (a saída do extract.py)

OUTPUT_DIR = Path("data/processed")
# ^ pasta onde vamos SALVAR o resultado já tratado

OUTPUT_FILE = OUTPUT_DIR / f"personagens_{ANIME_ID}_tratado.json"

# carregar o JSON bruto do disco

def carregar_dados(caminho: Path) -> dict:
    """Lê o arquivo JSON bruto e devolve como dicionário Python."""

    if not caminho.exists():
        # .exists() verifica se o arquivo realmente existe antes de tentar abrir
        # isso evita um erro feio caso o extract.py não tenha rodado ainda
        raise FileNotFoundError(
            f"Arquivo {caminho} não encontrado. Rode o extract.py primeiro."
        )

    with open(caminho, "r", encoding="utf-8") as f:
        # "r" = modo leitura (read)
        dados = json.load(f)
        # json.load lê o conteúdo do arquivo e converte pra dict/list Python

    logger.info(f"Dados brutos carregados de: {caminho}")
    return dados


# classificar por popularidade 

def categorizar_popularidade(favoritos: int) -> str:
    """Define uma categoria textual com base no número de favoritos."""

    # essa função existe separada só pra deixar a lógica de negócio isolada
    # e fácil de testar/ajustar sem mexer no resto do código

    if favoritos >= 5000:
        return "alta"
    elif favoritos >= 500:
        return "media"
    else:
        return "baixa"


# --- FUNÇÃO 3: transformar a lista de personagens ---

def transformar_personagens(dados_brutos: dict) -> list[dict]:
    """
    Recebe o dicionário bruto da API e devolve uma LISTA de dicionários
    já limpos, só com os campos que interessam.
    """

    lista_bruta = dados_brutos.get("data", [])
    # pega a lista de personagens dentro da chave "data"
    # (mesma lógica de segurança usada no extract.py: se não existir, usa lista vazia)

    logger.info(f"Transformando {len(lista_bruta)} registros...")

    personagens_tratados = []
    # lista vazia que vai receber cada personagem já tratado

    nomes_vistos = set()
    # um "set" (conjunto) guarda valores sem repetição
    # vamos usar isso pra detectar e pular nomes duplicados

    for item in lista_bruta:
        # percorre cada personagem da lista bruta, um de cada vez

        personagem_bruto = item.get("character", {})
        # dentro de cada "item" da Jikan, os dados do personagem ficam
        # aninhados na chave "character" - se não existir, usa dict vazio

        nome = personagem_bruto.get("name", "").strip()
        # .get("name", "") -> pega o nome, ou string vazia se não existir
        # .strip() -> remove espaços em branco extras no início/fim
        # (isso é a "normalização" que combinamos: nomes limpos e consistentes)

        if not nome:
            # se o nome ficou vazio depois de limpar, pula esse registro
            logger.warning("Personagem sem nome encontrado - ignorando registro")
            continue
            # "continue" pula pro próximo item do "for", sem executar o resto do bloco

        nome_normalizado = nome.lower()
        # .lower() deixa tudo minúsculo - usamos isso só pra COMPARAR duplicatas
        # (evita considerar "Tanjiro" e "tanjiro" como pessoas diferentes)

        if nome_normalizado in nomes_vistos:
            # se esse nome (em minúsculo) já apareceu antes, é duplicata
            logger.warning(f"Duplicata encontrada e ignorada: {nome}")
            continue

        nomes_vistos.add(nome_normalizado)
        # registra esse nome como "já visto" pra próxima verificação

        favoritos = item.get("favorites", 0)
        # número de favoritos vem no nível de "item", não dentro de "character"
        # valor padrão 0 caso não exista

        papel = item.get("role", "Desconhecido")
        # "role" indica se é Main (principal) ou Supporting (secundário)

        imagem_url = (
            personagem_bruto.get("images", {})
            .get("jpg", {})
            .get("image_url", "")
        )
        # esse encadeamento de .get() navega por 3 níveis do JSON:
        # images -> jpg -> image_url
        # usar .get() em cada nível (em vez de colchetes []) evita erro
        # caso algum desses níveis não exista na resposta da API

        personagem_tratado = {
            "nome": nome,
            "papel": papel,
            "favoritos": favoritos,
            "categoria_popularidade": categorizar_popularidade(favoritos),
            "imagem_url": imagem_url,
        }
        # monta um dicionário novo, limpo, só com os campos que decidimos manter
        # essa é a essência do "transform": moldar o dado bruto no formato que queremos

        personagens_tratados.append(personagem_tratado)
        # adiciona o dicionário tratado na lista final

    logger.info(f"Transformação concluída: {len(personagens_tratados)} registros válidos")
    return personagens_tratados


# --- FUNÇÃO 4: salvar o resultado tratado ---

def salvar_tratado(dados: list[dict], caminho: Path) -> None:
    """Salva a lista de personagens tratados em um novo arquivo JSON."""

    caminho.parent.mkdir(parents=True, exist_ok=True)
    # cria a pasta de destino (data/processed) se ainda não existir

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    logger.info(f"Dados tratados salvos em: {caminho}")


# --- FUNÇÃO PRINCIPAL ---

def main():
    dados_brutos = carregar_dados(INPUT_FILE)
    # etapa 1: carrega o que o extract.py salvou

    personagens_tratados = transformar_personagens(dados_brutos)
    # etapa 2: aplica toda a lógica de limpeza/transformação

    salvar_tratado(personagens_tratados, OUTPUT_FILE)
    # etapa 3: grava o resultado final em disco, pronto pro Load


if __name__ == "__main__":
    main()