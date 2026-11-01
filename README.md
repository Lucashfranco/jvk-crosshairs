# JVK Crosshairs

Miras dos pro players de CS2, extraídas das demos das partidas. Projeto da JVK Performance.

## Estrutura

- `pipeline/`: Python. Decodifica códigos de mira (`jvk_pipeline/sharecode.py`), extrai a mira de cada jogador de uma demo `.dem` com o demoparser2 (`jvk_pipeline/extract.py`) e roda o job semanal (`jvk_pipeline/publish.py`).
- `supabase/migrations/`: esquema do banco (times, jogadores, miras, envios, partidas processadas, execuções).
- `web/`: front-end Next.js 16 + Tailwind. Sem as variáveis de `web/.env.example` usa dados de exemplo (`npm --prefix web run dev`).
- `.github/workflows/publicar.yml`: job semanal (segunda, 06:00 de Brasília), também disparável à mão.

## Como as miras chegam ao site

1. **Times e elencos**: o job semanal lê o top 20 do [Valve Regional Standings](https://github.com/ValveSoftware/counter-strike_regional_standings), cria os times e jogadores novos e move quem trocou de time.
2. **Liquipedia**: o job busca a seção "Crosshair table" da página de cada jogador pela API do Liquipedia (até 50 páginas por requisição, uma requisição a cada 2,5 s, User-Agent identificado, como pedem os [termos](https://liquipedia.net/api-terms-of-use)). A mira só é aceita se o time da página bater com o do VRS, porque há nicks repetidos. O conteúdo é CC BY-SA: o site mostra "Fonte: Liquipedia" com link em cada mira. Uso permitido para site **não comercial**.
3. **Envio**: qualquer pessoa manda o código da mira de um jogador em `/enviar`. O site confere o código antes de gravar e o banco só aceita envios `pendente` vindos do público.
4. **Revisão**: no Supabase, Table Editor → `submissions`, troque `status` para `aprovado` ou `rejeitado` (o campo `note` guarda o motivo).
5. **Publicação**: o job decodifica os envios aprovados, grava a mira (`crosshairs`) e marca o envio como `publicado`, ou `invalido` se o código não decodificar. Cada execução fica em `pipeline_runs`.

A mira mostrada é a vista mais recentemente: a do Liquipedia leva a data da referência dela, a de um envio leva a data da publicação.
O site guarda as consultas em cache por até 1 hora, então uma mira publicada aparece em até 1 hora depois do job.

### Secrets do GitHub Actions

- `SUPABASE_URL`: `https://<ref>.supabase.co`
- `SUPABASE_SERVICE_KEY`: a chave **secret** do Supabase (Settings → API Keys). Nunca vai para o site nem para o repositório.

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
