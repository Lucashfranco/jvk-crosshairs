# Twitch — como usar

## 1. Painel da descrição (`painel-twitch.png`)
No canal: **Painel do criador › Configurações › Canal › Painéis** (ou "Editar painéis" abaixo da live) › **Adicionar um painel de texto ou imagem**.

- **Título do painel:** deixe em branco (a imagem já tem tudo)
- **Imagem:** `painel-twitch.png` (640x940; a Twitch mostra em 320 de largura, então fica nítido)
- **Link da imagem:** `https://jvk-crosshairs.vercel.app`
- **Descrição** (texto abaixo da imagem):

```
**JVK Crosshairs** — a mira dos pros no seu CS2.
As miras dos 100 jogadores do top 20 da Valve, com o código CS… pronto pra copiar e colar no jogo. Atualizado toda semana. Grátis.

🎯 [Ver as miras dos pros](https://jvk-crosshairs.vercel.app)
```

## 2. Faixa na tela da live
Feita para live em 1920x1080, tamanho real 900x160, fundo transparente. Arraste para um canto que não cubra o HUD do jogo.

- **Animada (recomendado):** no OBS, **Fontes › + › Navegador** › marque **Arquivo local** › escolha `overlay.html`, largura **900**, altura **160**. A mira do quadro troca de pro (donk, ZywOo, m0NESY, NiKo, ropz, FalleN) a cada 4 s e a borda pulsa de leve. Precisa da pasta inteira (`base.css` e `miras.js` junto).
- **Estática:** no OBS, **Fontes › + › Imagem** › escolha `overlay-live.png`.

## 3. Comando no chat (opcional, Nightbot / StreamElements)
```
!addcom !mira Miras dos pros de CS2 com o código pronto pra copiar: https://jvk-crosshairs.vercel.app
```

## Editar
As artes são geradas de `painel.html` e `overlay.html` (mesmas fontes e cores do site); as miras mostradas ficam em `miras.js`. Peça ao Claude para mudar o texto e gerar de novo.
