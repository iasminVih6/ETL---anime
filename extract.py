"""
Etapa 1: Extrair os dados
Buscar os personagens de um anime na API da Jikan (jikan.moe) e salva a resposta bruta em JSON
"""

import requests #biblioteca para fazer aquisições do HTTP ( o GET dessa API)
import json #biblioteca padrão do python para ler/escrever arquivos python
import time #biblioteca  para função de esperar os segundos
import logging #biblioteca padrão para registrar mensagens de log
from pathlib import Path  #biblioteca para trabalhar com caminhos de arquivos

#configuração de log ( bem basica)
logging.basicConfig(
    level=logging.INFO, #nivel minimo de msgs que sera exibida (INFO, WARNING, ERROR...)
    format="%(asctime)s [%(levelname)s] %(message)s" #formtato: hora (nivel) mensagem  
)

logger = logging.getLogger(__name__) #cria um logger especifico para esse arquivo

#CONFIG DO PIPELINE

ANIME_ID = 40748 #id demon slayer

BASE_URL = f"https://api.jikan.moe/v4/anime/{ANIME_ID}/characteres" #o f no começo é oara criar um s string e a variavel anime_id e substituida pelo valor da variavel

OUTPUT_DIR = Path("data/raw") #define a pasta onde o json bruto vai ser salvo

OUTPUT_FILE = OUTPUT_DIR / f"personagens_{ANIME_ID}.json" #juntar as pastas e obter data/raw/personagens...json


#FUNÇÃO 1: Buscar dados na API

def buscar_personagens(url: str, tentativas: int = 3) -> dict: #-> dict indica que a função deve retornar um dicionario (json virado ojeto python

    """
    fazer aquisição para a API, com retry siples em caso de erro (a jikan tem rate de limit e pode responder 429 - too many requests)
    """
    for tentativas in range(1, tentativas + 1): #1, tentativas + 1 gera os numeros 1,2,3 ( se tentativas = 3)
        logger.info(f"tentativa {tentativa} de {tentativa} - GET {url}") #registra no log qual tentativa está fazendo

        try:
            resposta = requests.get(url, timeout=10) #faz aquisição GET (buscar dados na web), timeout de 10 segs -- se API n responder nesse tempo, desiste e gera um erro

            if resposta.status_code == 200: #status 200 = OK, sem erros
               logger.info("Requisição bem sucedida")
               return resposta.json #retun para encerrar a fuunção e o .json que converte o texto da resposta em dicionario python

            elif resposta.status_code == 429: #status too many requests (limite do range)
                 espera = 3 * tentativas #calcula o quanto tempo espera em cada tentativa
                 logger.warning(f"Rate limit atingido. Esperando {espera}s...")
                 time.sleep(espera) #pausa para expera

            else:
                logger.error(f"Erro. Status {resposta.status_code}")
                resposta.raise_for_status()


        except requests.exceptions.RequestException as e:

            logger.erro(f"Falha na requisição: {e}") #variavel "e" guarda o erro
            time.sleep(2) #2 segundos antes de teentar dnv


    raise RuntimeError("Não foi possivel obter os dados após varias tentativas") #raise interrompe o programa lançando um erro personalizado

#FUNÇÇÃO 2: Salvar o json bruto em disco

def salvar_bruto(dados: dict, caminho: Path) -> None: #dict espera receber oq a função 1 retornou, path esperar receber o locan onde salvar
    caminho.parent.mkdir(parents=True, exist_ok=True)
    #caminho.parent = pega a pasta que contem o arquivo (ex: data/raw)
    #.mkdir() cria a pasta
    #parents = true -- cria pastas intermediarias

    with open(caminho, "w", encoding="utf-8") as f: #abre o arquivo no modo escrita "w". Encondig garante a sintaxe correta. With garante quee o arquivo sera fehcado automaticamente no fim do bloco
        json.dump(dados, f, ensure_ascii=False, indent=2)
        #json dump escreve o dicionario dados no arquivo f como JSON. Ensure mantem acentos legiveis. Ident formata o JSON com 2 espaços de identação

    logger.info(f"Dados brutos salvos em: {caminho}")



#FUNÇÃO MAIN

def main():
    dados = buscar_personagens(BASE_URL)
    #chama a função 1 passando a URL configurada
    #guarda o resultado (dicionario) na varival "dados"

    quantidade = len(dados.get("data", []))
    #dados.get pega a chave "data" do dicionario, pq a Jikan retorna os personganes dentro de uma chave chamada
    #se a chave n existir ela usa uma lista vazia [] como padrao
    #len conta quantos itens tem nessa lista

    logger.info(f"Total de personagens extraidos" {quantidade}) #loga quantos personagens vieram na resposta

    salvar_bruto(dados, OUTPUT_FILE) #chama a função 2, passando os dados e o caminho de onde salvar



#PONTO DE ENTRADA DO SCRIPT

if __name__ == "__main__": # condição de segurança para rodar o script

    main()
        
    