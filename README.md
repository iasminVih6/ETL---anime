# ETL - Personagens de Anime (Jikan API)

Pipeline de ETL (Extract, Transform, Load) em Python que busca dados de personagens de anime na [Jikan API](https://jikan.moe) (API não-oficial do MyAnimeList), trata esses dados e carrega num banco SQLite.

Projeto criado com o apoio do claude, sendo um exercício de aprendizado de conceitos de ETL, consumo de APIs REST, tratamento de dados e persistência em banco de dados.

## O que o projeto faz

```
API Jikan  →  extract.py  →  JSON bruto  →  transform.py  →  JSON tratado  →  load.py  →  SQLite
```

1. **Extract**: busca a lista de personagens de um anime na Jikan API e salva a resposta crua em JSON
2. **Transform**: limpa os dados (remove duplicatas, normaliza nomes, descarta registros inválidos) e classifica cada personagem por popularidade
3. **Load**: carrega os dados tratados numa tabela SQLite

## Pré-requisitos

- Python 3.9 ou superior
- pip

## Instalação

```bash
git clone <url-do-seu-repositorio>
cd ETL---anime
pip install -r requirements.txt
```

## Como rodar

Execute os três scripts em ordem, na mesma pasta:

```bash
python extract.py
python transform.py
python load.py
```

Cada script depende do arquivo gerado pelo anterior. Ao final, você terá:

```
data/
├── raw/
│   └── personagens_38000.json        # saída do extract.py
├── processed/
│   └── personagens_38000_tratado.json  # saída do transform.py
└── etl_desafio.db                     # saída do load.py (banco SQLite)
```

## Trocando de anime

Edite a constante `ANIME_ID` no topo de **cada um dos três arquivos** (`extract.py`, `transform.py`, `load.py`) — os três precisam usar o mesmo ID pra se encontrarem nos arquivos intermediários. O ID é o número que aparece na URL do anime no MyAnimeList, por exemplo:

```
https://myanimelist.net/anime/38000/Kimetsu_no_Yaiba
                         ^^^^^
                    esse é o ID
```

## Estrutura do projeto

| Arquivo | Descrição |
|---|---|
| `extract.py` | Busca os personagens na API e salva o JSON bruto |
| `extract_comentado.py` | Mesma lógica do extract.py, com comentário explicativo em praticamente toda linha (versão de estudo) |
| `transform.py` | Limpa e transforma o JSON bruto |
| `load.py` | Carrega os dados tratados no SQLite |
| `requirements.txt` | Dependências do projeto |
| `data/` | Pasta gerada automaticamente com os dados em cada etapa (não versionar no git) |

Para uma explicação técnica mais detalhada de cada etapa e das decisões de projeto, veja [DOCUMENTACAO.md](DOCUMENTACAO.md).

## Problema conhecido: erro 504 na Jikan API

O endpoint `/anime/{id}/characters` da Jikan API pode retornar erro 504 (`Gateway Time-out`) de forma intermitente. Isso acontece quando o servidor da Jikan não consegue se conectar ao MyAnimeList para buscar os dados — é um problema do lado deles, não do código deste projeto. Se isso acontecer, espere alguns minutos e tente rodar `extract.py` novamente. Mais detalhes em [DOCUMENTACAO.md](DOCUMENTACAO.md#troubleshooting).

## Tecnologias usadas

- Python 3
- [requests](https://docs.python-requests.org/) — chamadas HTTP
- `sqlite3` (biblioteca padrão) — banco de dados
- `json`, `logging`, `pathlib` (biblioteca padrão)

## Próximos passos (ideias de evolução)

- [ ] Unificar os três scripts num `main.py` que roda o pipeline completo
- [ ] Adicionar testes automatizados (pytest) para a função de transformação
- [ ] Expor os dados carregados através de uma API própria (FastAPI/Flask)
- [ ] Agendar a execução periódica do pipeline
