# JVK Crosshairs

Miras dos pro players de CS2, extraídas das demos das partidas. Projeto da JVK Performance.

## Estrutura

- `pipeline/`: Python. Decodifica códigos de mira (`jvk_pipeline/sharecode.py`) e extrai a mira de cada jogador de uma demo `.dem` com o demoparser2 (`jvk_pipeline/extract.py`).
- `supabase/migrations/`: esquema do banco (times, jogadores, miras, partidas processadas, execuções).
- `web/`: front-end Next.js 16 + Tailwind. Sem as variáveis de `web/.env.example` usa dados de exemplo (`npm --prefix web run dev`).

## Formatos de código de mira

Desde a atualização de 30/09/2026 o CS2 gera códigos `CS` + 44 caracteres e não importa mais os
códigos `CSGO-xxxxx-...`. O decodificador entende os dois; o site mostra o código como veio da demo
e sempre oferece os comandos de console, que funcionam em qualquer caso.

## Rodando os testes

```bash
py -3 -m venv .venv
.venv/Scripts/pip install -r pipeline/requirements.txt
cd pipeline && ../.venv/Scripts/python -m pytest -q
```

Para incluir o teste com uma demo real, defina `JVK_TEST_DEMO` com o caminho de um `.dem`.

Os vetores de `pipeline/tests/fixtures/crosshair_vectors.json` foram gerados com a biblioteca
[csgo-sharecode](https://github.com/akiver/csgo-sharecode) 7.0.1 (MIT), da qual o decodificador é um porte.

## Fonte das demos

Os Termos de Uso do HLTV (item 2.2) proíbem scraping, e o robots.txt bloqueia `/download/demo*`.
O pipeline não acessa o HLTV de forma automatizada sem autorização.
