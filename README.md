# Automação de cadastro de memorandos (IPM)

Este repositório agora contém um **bot de extração automática** que recebe a imagem do memorando e devolve os campos prontos para preencher no sistema:

- número/ano do memorando
- secretaria solicitante
- texto para o campo grande (`Usuario(s)`)
- quem executou/liberou (campo `Recebido por`)
- data de emissão
- data de realização

## Como funciona

1. Você envia uma imagem (`.png`, `.jpg`, `.jpeg` ou `.webp`) do memorando.
2. O script usa o modelo multimodal do Gemini para ler e estruturar os dados.
3. Ele devolve um JSON validado e um resumo para copiar/colar no formulário.

## Pré-requisitos

- Python 3.10+
- Chave de API do Gemini em variável de ambiente:

```bash
export GEMINI_API_KEY="sua_chave"
```

- Dependência:

```bash
pip install google-genai
```

## Uso

```bash
python memorando_bot.py --imagem ./memorando_exemplo.png
```

Opções úteis:

- `--modelo gemini-2.5-flash` (padrão)
- `--saida-json resultado.json` para salvar saída estruturada
- `--sem-relatorio` para imprimir apenas o JSON

## Exemplo de saída (resumo)

```text
NÚMERO: 023
ANO: 2026
SECRETARIA: Secretaria Municipal de Planejamento e Inovação Tecnológica
DATA EMISSÃO: 2026-04-15
DATA REALIZAÇÃO: 2026-04-16
RECEBIDO POR: Equipe T.I. / servidor responsável pela liberação

TEXTO PARA CAMPO "Usuario(s)":
Memorando n.º 023/2026 - solicitação de privilégios no Sistema IPM para ...
```

## Integração prática com seu fluxo

Você pode criar um atalho/bot (Telegram, WhatsApp Business API, Discord, etc.) que:

1. recebe a imagem,
2. chama este script,
3. retorna os campos já organizados para preenchimento.

Assim você elimina o trabalho manual de leitura e digitação repetitiva.
