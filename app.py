from flask import Flask, render_template, redirect, url_for, session, request
import requests
import sqlite3
import json
from datetime import datetime

from config import (
    DISCORD_CLIENT_ID,
    DISCORD_CLIENT_SECRET,
    DISCORD_REDIRECT_URI,
    OWNER_ID,
    BOT_TOKEN,
    FLASK_SECRET_KEY,
    PORT,
    STAFF_ROLE_ID,
    DISCORD_GUILD_ID,
)

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

DATABASE = "staff.db"

QUESTIONS = [
    {"key": "experiencia", "question": "Você já teve experiência como staff em algum servidor?", "options": [
        ("0", "Nunca tive experiência e não sei como funciona uma equipe de staff."),
        ("1", "Já tive pouca experiência ou conheço parcialmente as funções."),
        ("2", "Já tive experiência ou conheço bem as responsabilidades de um staff."),
    ]},
    {"key": "moderacao", "question": "Como você agiria diante de uma discussão entre membros?", "options": [
        ("0", "Ignoraria a situação ou escolheria um lado sem analisar."),
        ("1", "Tentaria acalmar a situação, mas pediria ajuda se ficasse difícil."),
        ("2", "Ouviria os envolvidos, analisaria o contexto e aplicaria as regras de forma imparcial."),
    ]},
    {"key": "regras", "question": "O que você faria ao encontrar um membro quebrando uma regra?", "options": [
        ("0", "Ignoraria a situação."),
        ("1", "Chamaria a atenção do membro e tentaria resolver."),
        ("2", "Identificaria a regra, analisaria a situação e aplicaria a punição adequada."),
    ]},
    {"key": "imparcialidade", "question": "Como você lidaria com um amigo que estivesse quebrando regras?", "options": [
        ("0", "Deixaria passar por ser meu amigo."),
        ("1", "Conversaria com ele e tentaria fazê-lo parar."),
        ("2", "Trataria o amigo da mesma maneira que qualquer outro membro e seguiria as regras."),
    ]},
    {"key": "atendimento", "question": "Como você atenderia um membro que estivesse com um problema?", "options": [
        ("0", "Ignoraria ou responderia de qualquer maneira."),
        ("1", "Tentaria ajudar, procurando outro staff caso necessário."),
        ("2", "Ouviria o problema, responderia com respeito e buscaria uma solução adequada."),
    ]},
    {"key": "responsabilidade", "question": "Como você demonstra responsabilidade dentro da equipe?", "options": [
        ("0", "Faria apenas o que tivesse vontade."),
        ("1", "Cumpriria algumas tarefas quando tivesse disponibilidade."),
        ("2", "Cumpriria minhas responsabilidades, respeitaria a equipe e avisaria quando não pudesse realizar algo."),
    ]},
    {"key": "atividade", "question": "Com que frequência você pretende estar ativo no servidor?", "options": [
        ("0", "Entraria raramente e não teria compromisso com a equipe."),
        ("1", "Estaria ativo algumas vezes durante a semana."),
        ("2", "Pretendo manter uma atividade frequente e acompanhar o servidor regularmente."),
    ]},
    {"key": "conflitos", "question": "Como você resolveria um conflito entre dois membros?", "options": [
        ("0", "Tomaria partido ou aumentaria a discussão."),
        ("1", "Tentaria conversar com os envolvidos para encerrar o conflito."),
        ("2", "Ouviria os dois lados, verificaria o que aconteceu e buscaria uma solução baseada nas regras."),
    ]},
    {"key": "decisao", "question": "O que faria se não soubesse como resolver uma situação?", "options": [
        ("0", "Tomaria qualquer decisão sem procurar orientação."),
        ("1", "Tentaria encontrar uma solução sozinho antes de pedir ajuda."),
        ("2", "Procuraria um staff responsável ou superior e seguiria a orientação correta."),
    ]},
    {"key": "equipe", "question": "Como você trabalharia em conjunto com os outros staffs?", "options": [
        ("0", "Preferiria trabalhar sozinho e não seguiria orientações da equipe."),
        ("1", "Trabalharia com a equipe quando fosse necessário."),
        ("2", "Manteria comunicação, respeitaria os outros staffs e colaboraria nas decisões."),
    ]},
    {"key": "motivacao", "question": "Por que você quer fazer parte da equipe de staff?", "options": [
        ("0", "Quero apenas o cargo ou os benefícios que ele oferece."),
        ("1", "Quero ajudar o servidor, mas ainda não sei exatamente como contribuir."),
        ("2", "Quero contribuir com a comunidade, ajudar os membros e colaborar para manter o servidor organizado."),
    ]},
]


def init_database():
    connection = sqlite3.connect(DATABASE)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT NOT NULL,
            username TEXT NOT NULL,
            global_name TEXT,
            score INTEGER NOT NULL,
            raw_score INTEGER NOT NULL,
            answers TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pendente',
            observation TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS admin_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluation_id INTEGER NOT NULL,
            admin_discord_id TEXT NOT NULL,
            admin_username TEXT,
            action TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def log_admin_action(evaluation_id, action):
    admin = session.get("user") or {}

    connection = sqlite3.connect(DATABASE)

    connection.execute("""
        INSERT INTO admin_actions (
            evaluation_id,
            admin_discord_id,
            admin_username,
            action,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        evaluation_id,
        str(admin.get("id", "")),
        admin.get("global_name")
        or admin.get("username")
        or "Administrador",
        action,
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    ))

    connection.commit()
    connection.close()


def save_evaluation(user, answers, score, raw_score):
    connection = sqlite3.connect(DATABASE)

    connection.execute("""
        INSERT INTO evaluations (
            discord_id,
            username,
            global_name,
            score,
            raw_score,
            answers,
            status,
            observation,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(user.get("id", "")),
        user.get("username", "Desconhecido"),
        user.get("global_name"),
        score,
        raw_score,
        json.dumps(answers, ensure_ascii=False),
        "Pendente",
        "",
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    ))

    connection.commit()
    connection.close()


def discord_authorize_url():
    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",
    }

    query = "&".join(
        f"{key}={requests.utils.quote(str(value))}"
        for key, value in params.items()
    )

    return f"https://discord.com/oauth2/authorize?{query}"


def get_discord_user(code):
    token_response = requests.post(
        "https://discord.com/api/oauth2/token",
        data={
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        timeout=15,
    )

    if not token_response.ok:
        print(
            "Erro OAuth2:",
            token_response.status_code,
            token_response.text
        )
        return None

    access_token = token_response.json().get("access_token")

    if not access_token:
        return None

    user_response = requests.get(
        "https://discord.com/api/users/@me",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        timeout=15,
    )

    if not user_response.ok:
        print(
            "Erro ao obter usuário:",
            user_response.status_code
        )
        return None

    return user_response.json()


def send_result_to_owner(user, answers, score):
    if not BOT_TOKEN or not OWNER_ID:
        print("OWNER_ID ou BOT_TOKEN não configurado.")
        return False

    lines = [
        "🛡️ **NOVA AVALIAÇÃO PARA STAFF**",
        "",
        f"👤 **Candidato:** {user.get('username', 'Desconhecido')}",
        f"🆔 **ID:** `{user.get('id', 'Desconhecido')}`",
        f"📊 **Pontuação:** **{score}/20**",
        "",
        "📝 **Respostas:**",
    ]

    for index, question_data in enumerate(QUESTIONS, 1):
        key = question_data["key"]
        question = question_data["question"]
        answer = answers.get(key, 0)

        try:
            answer = int(answer)
        except (ValueError, TypeError):
            answer = 0

        selected_text = "Resposta não encontrada"

        for value, label in question_data["options"]:
            if int(value) == answer:
                selected_text = label
                break

        lines.append(
            f"**{index}.** {answer}/2\n"
            f"❓ {question}\n"
            f"💬 {selected_text}"
        )

    content = "\n\n".join(lines)

    chunks = [
        content[i:i + 1900]
        for i in range(0, len(content), 1900)
    ]

    try:
        dm_response = requests.post(
            "https://discord.com/api/v10/users/@me/channels",
            headers={
                "Authorization": f"Bot {BOT_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "recipient_id": str(OWNER_ID)
            },
            timeout=15,
        )

        if not dm_response.ok:
            print(
                "Erro ao criar DM:",
                dm_response.status_code,
                dm_response.text
            )
            return False

        channel_id = dm_response.json().get("id")

        if not channel_id:
            return False

        for chunk in chunks:
            message_response = requests.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers={
                    "Authorization": f"Bot {BOT_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "content": chunk
                },
                timeout=15,
            )

            if not message_response.ok:
                print(
                    "Erro ao enviar DM:",
                    message_response.status_code,
                    message_response.text
                )
                return False

        return True

    except requests.RequestException as error:
        print("Erro de conexão com Discord:", error)
        return False


def add_staff_role(discord_id):
    if not BOT_TOKEN or not DISCORD_GUILD_ID or not STAFF_ROLE_ID:
        return False, "Configuração do Discord incompleta."

    url = (
        f"https://discord.com/api/v10/guilds/{DISCORD_GUILD_ID}"
        f"/members/{discord_id}/roles/{STAFF_ROLE_ID}"
    )

    try:
        response = requests.put(
            url,
            headers={
                "Authorization": f"Bot {BOT_TOKEN}"
            },
            timeout=15,
        )

    except requests.RequestException as error:
        return False, f"Erro de conexão com o Discord: {error}"

    if response.status_code == 204:
        return True, "Cargo Staff adicionado com sucesso."

    if response.status_code == 404:
        return False, (
            "Usuário não encontrado no servidor ou o servidor/cargo "
            "informado não foi encontrado."
        )

    if response.status_code == 403:
        return False, (
            "O bot não tem permissão para adicionar esse cargo. "
            "Verifique 'Gerenciar Cargos' e a hierarquia dos cargos."
        )

    return (
        False,
        f"Discord retornou HTTP {response.status_code}: "
        f"{response.text[:300]}"
    )


@app.route("/")
def index():
    user = session.get("user")

    return render_template(
        "index.html",
        user=user,
        login_url=discord_authorize_url()
    )


@app.route("/login")
def login():
    return redirect(discord_authorize_url())


@app.route("/callback")
def callback():
    code = request.args.get("code")

    if not code:
        return redirect(url_for("index"))

    user = get_discord_user(code)

    if not user:
        return "Não foi possível fazer login com o Discord.", 400

    session["user"] = {
        "id": user.get("id"),
        "username": user.get("username"),
        "global_name": user.get("global_name"),
        "avatar": user.get("avatar"),
    }

    return redirect(url_for("teste"))


@app.route("/teste", methods=["GET", "POST"])
def teste():
    user = session.get("user")

    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        answers = {}
        raw_score = 0

        for question_data in QUESTIONS:
            key = question_data["key"]
            value = request.form.get(key, "0")

            try:
                value = int(value)
            except (ValueError, TypeError):
                value = 0

            value = max(0, min(2, value))

            answers[key] = value
            raw_score += value

        score = round((raw_score / 22) * 20)
        score = max(0, min(20, score))

        save_evaluation(
            user,
            answers,
            score,
            raw_score
        )

        session["last_result"] = {
            "score": score,
            "max_score": 20,
            "raw_score": raw_score,
            "answers": answers,
        }

        send_result_to_owner(
            user,
            answers,
            score
        )

        return redirect(url_for("resultado"))

    return render_template(
        "test.html",
        user=user,
        questions=QUESTIONS
    )


@app.route("/resultado")
def resultado():
    user = session.get("user")
    result = session.get("last_result")

    if not user:
        return redirect(url_for("login"))

    if not result:
        return redirect(url_for("teste"))

    score = result["score"]

    if score >= 16:
        status = "Pontuação alta"
    elif score >= 10:
        status = "Pontuação intermediária"
    else:
        status = "Pontuação baixa"

    return render_template(
        "result.html",
        user=user,
        result=result,
        status=status
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


init_database()


# =========================================================
# PAINEL ADMINISTRATIVO — STAFF
# =========================================================

def is_owner():
    user = session.get("user")

    if not user:
        return False

    return str(user.get("id")) == str(OWNER_ID)


@app.route("/admin")
def admin_panel():
    if not session.get("user"):
        return redirect(url_for("login"))

    if not is_owner():
        return "Acesso negado.", 403

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    evaluations = conn.execute(
        "SELECT * FROM evaluations ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        evaluations=evaluations
    )


@app.route("/admin/avaliacao/<int:evaluation_id>")
def admin_evaluation(evaluation_id):
    if not session.get("user"):
        return redirect(url_for("login"))

    if not is_owner():
        return "Acesso negado.", 403

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    evaluation = conn.execute(
        "SELECT * FROM evaluations WHERE id = ?",
        (evaluation_id,)
    ).fetchone()

    actions = conn.execute(
        """
        SELECT * FROM admin_actions
        WHERE evaluation_id = ?
        ORDER BY id DESC
        """,
        (evaluation_id,)
    ).fetchall()

    conn.close()

    if not evaluation:
        return "Avaliação não encontrada.", 404

    try:
        answers = json.loads(
            evaluation["answers"]
        )
    except (json.JSONDecodeError, TypeError):
        answers = {}

    return render_template(
        "admin_evaluation.html",
        evaluation=evaluation,
        answers=answers,
        questions=QUESTIONS,
        actions=actions
    )


@app.route(
    "/admin/avaliacao/<int:evaluation_id>/aprovar",
    methods=["POST"]
)
def approve_evaluation(evaluation_id):
    if not session.get("user"):
        return redirect(url_for("login"))

    if not is_owner():
        return "Acesso negado.", 403

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    evaluation = conn.execute(
        "SELECT * FROM evaluations WHERE id = ?",
        (evaluation_id,)
    ).fetchone()

    if not evaluation:
        conn.close()
        return "Avaliação não encontrada.", 404

    if evaluation["status"] == "Aprovado":
        conn.close()

        return redirect(
            url_for(
                "admin_evaluation",
                evaluation_id=evaluation_id
            )
        )

    success, message = add_staff_role(
        evaluation["discord_id"]
    )

    if not success:
        conn.close()

        return (
            f"<h2>Não foi possível aprovar o candidato.</h2>"
            f"<p>{message}</p>"
            f'<p><a href="{url_for("admin_evaluation", evaluation_id=evaluation_id)}">'
            "Voltar para a avaliação</a></p>",
            400,
        )

    observation = (
        "Candidato aprovado. Cargo de Staff adicionado automaticamente."
    )

    conn.execute(
        """
        UPDATE evaluations
        SET status = ?, observation = ?
        WHERE id = ?
        """,
        (
            "Aprovado",
            observation,
            evaluation_id
        ),
    )

    conn.commit()
    conn.close()

    log_admin_action(
        evaluation_id,
        "Aprovado"
    )

    return redirect(
        url_for(
            "admin_evaluation",
            evaluation_id=evaluation_id
        )
    )


@app.route(
    "/admin/avaliacao/<int:evaluation_id>/excluir",
    methods=["POST"]
)
def delete_evaluation(evaluation_id):
    if not session.get("user"):
        return redirect(url_for("login"))

    if not is_owner():
        return "Acesso negado.", 403

    conn = sqlite3.connect(DATABASE)

    evaluation = conn.execute(
        "SELECT id FROM evaluations WHERE id = ?",
        (evaluation_id,)
    ).fetchone()

    if not evaluation:
        conn.close()
        return "Avaliação não encontrada.", 404

    log_admin_action(
        evaluation_id,
        "Excluído"
    )

    conn.execute(
        "DELETE FROM evaluations WHERE id = ?",
        (evaluation_id,)
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for("admin_panel")
    )


@app.route(
    "/admin/avaliacao/<int:evaluation_id>/recusar",
    methods=["POST"]
)
def reject_evaluation(evaluation_id):
    if not session.get("user"):
        return redirect(url_for("login"))

    if not is_owner():
        return "Acesso negado.", 403

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    evaluation = conn.execute(
        "SELECT * FROM evaluations WHERE id = ?",
        (evaluation_id,)
    ).fetchone()

    if not evaluation:
        conn.close()
        return "Avaliação não encontrada.", 404

    if evaluation["status"] == "Aprovado":
        conn.close()
        return (
            "Este candidato já foi aprovado e recebeu o cargo Staff.",
            400
        )

    conn.execute(
        """
        UPDATE evaluations
        SET status = ?, observation = ?
        WHERE id = ?
        """,
        (
            "Recusado",
            "Candidato recusado pela administração.",
            evaluation_id
        ),
    )

    conn.commit()
    conn.close()

    log_admin_action(
        evaluation_id,
        "Recusado"
    )

    return redirect(
        url_for(
            "admin_evaluation",
            evaluation_id=evaluation_id
        )
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )