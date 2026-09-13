"""
ETL - Etapa 3: LOAD
Lê o JSON já tratado pelo transform.py e carrega os registros
num banco de dados SQLite.

Versão COMENTADA LINHA A LINHA para estudo.
"""

# --- IMPORTS ---

import json        # pra ler o arquivo JSON tratado
import sqlite3      # biblioteca padrão do Python pra trabalhar com SQLite (não precisa instalar nada)
import logging      # pra registrar o progresso da carga
from pathlib import Path


# --- CONFIGURAÇÃO DO LOG ---

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# --- CONFIGURAÇÕES DO PIPELINE ---

ANIME_ID = 40748

INPUT_FILE = Path("data/processed") / f"personagens_{ANIME_ID}_tratado.json"
# ^ de onde vamos LER (a saída do transform.py)

DB_FILE = Path("data") / "etl_desafio.db"
# ^ arquivo do banco SQLite (se não existir, o sqlite3 cria automaticamente)


# --- FUNÇÃO 1: carregar o JSON tratado do disco ---

def carregar_dados_tratados(caminho: Path) -> list[dict]:
    """Lê o JSON já tratado e devolve como lista de dicionários."""

    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo {caminho} não encontrado. Rode o transform.py primeiro."
        )

    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)

    logger.info(f"{len(dados)} registros tratados carregados de: {caminho}")
    return dados


# --- FUNÇÃO 2: garantir que a tabela existe ---

def criar_tabela(conexao: sqlite3.Connection) -> None:
    """Cria a tabela 'personagens' no banco, caso ainda não exista."""

    # "conexao" é o objeto que representa a ligação aberta com o banco
    # a partir dele conseguimos executar comandos SQL

    cursor = conexao.cursor()
    # o "cursor" é o objeto usado pra EXECUTAR comandos SQL de fato
    # (a conexão abre o "canal", o cursor "fala" com o banco por esse canal)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            papel TEXT,
            favoritos INTEGER,
            categoria_popularidade TEXT,
            imagem_url TEXT
        )
    """)
    # CREATE TABLE IF NOT EXISTS -> só cria se a tabela ainda não existir
    # id INTEGER PRIMARY KEY AUTOINCREMENT -> chave única que o próprio
    # SQLite gera automaticamente pra cada linha (1, 2, 3...)
    #
    # nome TEXT NOT NULL -> campo obrigatório, não pode ficar vazio
    #
    # os demais campos batem exatamente com o dicionário que o
    # transform.py produziu

    conexao.commit()
    # commit() confirma (salva de vez) as alterações feitas no banco
    # sem isso, o CREATE TABLE poderia não ser persistido

    logger.info("Tabela 'personagens' verificada/criada com sucesso")


# --- FUNÇÃO 3: inserir os dados na tabela ---

def inserir_personagens(conexao: sqlite3.Connection, personagens: list[dict]) -> None:
    """Insere cada personagem tratado na tabela do banco."""

    cursor = conexao.cursor()

    # antes de inserir, limpamos a tabela - isso torna o pipeline
    # "idempotente": rodar de novo não gera duplicatas acumuladas
    cursor.execute("DELETE FROM personagens")
    logger.info("Tabela limpa antes da nova carga (evita duplicar dados)")

    total_inseridos = 0
    # contador simples pra sabermos quantos registros realmente entraram

    for personagem in personagens:
        # percorre cada dicionário da lista tratada

        cursor.execute(
            """
            INSERT INTO personagens (nome, papel, favoritos, categoria_popularidade, imagem_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                personagem["nome"],
                personagem["papel"],
                personagem["favoritos"],
                personagem["categoria_popularidade"],
                personagem["imagem_url"],
            )
        )
        # os "?" são PLACEHOLDERS - o sqlite3 substitui cada um pelo valor
        # correspondente da tupla logo abaixo
        #
        # IMPORTANTE: nunca monte esse SQL concatenando strings
        # (tipo f"INSERT INTO ... VALUES ('{nome}')") - isso abre brecha
        # pra SQL Injection. Usar "?" é a forma segura e correta.

        total_inseridos += 1
        # += 1 é o mesmo que "total_inseridos = total_inseridos + 1"

    conexao.commit()
    # confirma todas as inserções de uma vez (mais eficiente que
    # dar commit a cada linha inserida)

    logger.info(f"{total_inseridos} personagens inseridos no banco")


# --- FUNÇÃO 4: conferir o resultado (opcional, útil pra debug) ---

def verificar_carga(conexao: sqlite3.Connection) -> None:
    """Consulta o banco e mostra um resumo simples no log, só pra conferência."""

    cursor = conexao.cursor()

    cursor.execute("SELECT COUNT(*) FROM personagens")
    # SELECT COUNT(*) conta quantas linhas existem na tabela

    total = cursor.fetchone()[0]
    # fetchone() pega UMA linha do resultado (aqui só tem uma: o total)
    # o resultado vem como tupla, tipo (2,) - por isso pegamos o [0]

    logger.info(f"Verificação: {total} registros na tabela 'personagens'")

    cursor.execute(
        "SELECT categoria_popularidade, COUNT(*) FROM personagens GROUP BY categoria_popularidade"
    )
    # GROUP BY agrupa as linhas por categoria e conta quantas tem em cada uma

    for categoria, quantidade in cursor.fetchall():
        # fetchall() pega TODAS as linhas do resultado, como lista de tuplas
        # o "for categoria, quantidade in ..." desempacota cada tupla (a, b)
        logger.info(f"  - {categoria}: {quantidade} personagem(ns)")


# --- FUNÇÃO PRINCIPAL ---

def main():
    personagens = carregar_dados_tratados(INPUT_FILE)
    # etapa 1: lê o JSON tratado

    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    # garante que a pasta "data/" existe antes de criar o banco dentro dela

    conexao = sqlite3.connect(DB_FILE)
    # abre (ou cria, se não existir) o arquivo de banco SQLite
    # a partir daqui "conexao" representa essa ligação aberta

    try:
        criar_tabela(conexao)
        # etapa 2: garante que a tabela existe

        inserir_personagens(conexao, personagens)
        # etapa 3: insere os dados

        verificar_carga(conexao)
        # etapa 4 (bônus): confere o que foi carregado

    finally:
        # "finally" executa SEMPRE, mesmo se algo der erro lá em cima
        conexao.close()
        # fecha a conexão com o banco - importante pra não deixar
        # o arquivo "travado" ou consumindo memória à toa
        logger.info("Conexão com o banco encerrada")


if __name__ == "__main__":
    main()