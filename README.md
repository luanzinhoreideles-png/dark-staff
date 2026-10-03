# DARK STAFF — Site de Avaliação

Site de avaliação para candidatos à equipe de Staff da DARK SHOP.

## Recursos

- Login com Discord
- 11 perguntas
- Cada pergunta vale até 2 pontos
- Pontuação final máxima: 20 pontos
- Resultado exibido no site
- Resultado enviado por DM para o dono
- Interface responsiva para celular
- Visual DARK

## Configuração

Edite o arquivo `config.py` e preencha:

- `DISCORD_CLIENT_ID`
- `DISCORD_CLIENT_SECRET`
- `DISCORD_REDIRECT_URI`
- `OWNER_ID`
- `BOT_TOKEN`
- `FLASK_SECRET_KEY`

## Redirect do Discord

No Discord Developer Portal, adicione:

`http://127.0.0.1:5000/callback`

em:

OAuth2 → Redirects

## Instalação

No Termux:

```bash
cd "/storage/emulated/0/dark_staff_site"
pip install -r requirements.txt