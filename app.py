import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
from pymongo.errors import PyMongoError

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave-local-para-desenvolvimento")
DATABASE = os.getenv("DATABASE_PATH", "chamados.db")

# MongoDB é configurado pela variável MONGO_URI.
# Se ela não estiver definida, o sistema continua funcionando no modo SQL,
# mas o histórico NoSQL ficará indisponível até configurar a conexão.
mongo_collection = None
mongo_error = None
mongo_uri = os.getenv("MONGO_URI")
if mongo_uri:
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        mongo_collection = client["suporte_tecnico"]["historicos"]
    except PyMongoError as exc:
        mongo_error = str(exc)


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS chamados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            equipamento TEXT NOT NULL,
            categoria_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Aberto',
            criado_em TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        );
        """)
        for categoria in ["Hardware", "Software", "Rede", "Acesso", "Outro"]:
            conn.execute("INSERT OR IGNORE INTO categorias (nome) VALUES (?)", (categoria,))


def registrar_historico(chamado_id, responsavel, acao, observacoes):
    if mongo_collection is None:
        return False
    documento = {
        "chamado_id": chamado_id,
        "data": datetime.now().astimezone().isoformat(timespec="seconds"),
        "responsavel": responsavel,
        "acao": acao,
        "observacoes": observacoes
    }
    try:
        mongo_collection.insert_one(documento)
        return True
    except PyMongoError:
        return False


@app.route("/")
def index():
    with get_db() as conn:
        chamados = conn.execute("""
            SELECT c.*, u.nome AS solicitante, cat.nome AS categoria
            FROM chamados c
            JOIN usuarios u ON u.id = c.usuario_id
            JOIN categorias cat ON cat.id = c.categoria_id
            ORDER BY c.id DESC
        """).fetchall()
    return render_template("index.html", chamados=chamados,
                           mongo_ok=mongo_collection is not None,
                           mongo_error=mongo_error)


@app.route("/novo", methods=["GET", "POST"])
def novo_chamado():
    with get_db() as conn:
        categorias = conn.execute("SELECT * FROM categorias ORDER BY nome").fetchall()
    if request.method == "POST":
        nome = request.form.get("solicitante", "").strip()
        equipamento = request.form.get("equipamento", "").strip()
        categoria_id = request.form.get("categoria_id", "")
        descricao = request.form.get("descricao", "").strip()
        if not all([nome, equipamento, categoria_id, descricao]):
            flash("Preencha todos os campos.", "erro")
            return render_template("novo.html", categorias=categorias)
        with get_db() as conn:
            usuario = conn.execute("SELECT id FROM usuarios WHERE nome = ?", (nome,)).fetchone()
            if usuario is None:
                cursor = conn.execute("INSERT INTO usuarios (nome) VALUES (?)", (nome,))
                usuario_id = cursor.lastrowid
            else:
                usuario_id = usuario["id"]
            cursor = conn.execute("""
                INSERT INTO chamados (usuario_id, equipamento, categoria_id, descricao, status, criado_em)
                VALUES (?, ?, ?, ?, 'Aberto', ?)
            """, (usuario_id, equipamento, int(categoria_id), descricao,
                  datetime.now().astimezone().isoformat(timespec="seconds")))
            chamado_id = cursor.lastrowid
        salvo = registrar_historico(chamado_id, nome, "Chamado criado", descricao)
        if salvo:
            flash(f"Chamado #{chamado_id} criado e registrado no histórico.", "sucesso")
        else:
            flash(f"Chamado #{chamado_id} criado no SQLite. Configure/verifique o MongoDB para registrar o histórico.", "aviso")
        return redirect(url_for("detalhe", chamado_id=chamado_id))
    return render_template("novo.html", categorias=categorias)


@app.route("/chamado/<int:chamado_id>", methods=["GET", "POST"])
def detalhe(chamado_id):
    with get_db() as conn:
        chamado = conn.execute("""
            SELECT c.*, u.nome AS solicitante, cat.nome AS categoria
            FROM chamados c
            JOIN usuarios u ON u.id = c.usuario_id
            JOIN categorias cat ON cat.id = c.categoria_id
            WHERE c.id = ?
        """, (chamado_id,)).fetchone()
    if chamado is None:
        flash("Chamado não encontrado.", "erro")
        return redirect(url_for("index"))

    if request.method == "POST":
        novo_status = request.form.get("status", "")
        comentario = request.form.get("comentario", "").strip()
        responsavel = request.form.get("responsavel", "").strip() or "Equipe de suporte"
        status_validos = ["Aberto", "Em andamento", "Concluído"]
        if novo_status not in status_validos:
            flash("Status inválido.", "erro")
        else:
            status_anterior = chamado["status"]
            with get_db() as conn:
                conn.execute("UPDATE chamados SET status = ? WHERE id = ?",
                             (novo_status, chamado_id))
            observacoes = comentario or f"Status alterado de {status_anterior} para {novo_status}."
            acao = "Status atualizado" if novo_status != status_anterior else "Comentário registrado"
            salvo = registrar_historico(chamado_id, responsavel, acao, observacoes)
            if salvo:
                flash("Atualização registrada no SQLite e no MongoDB.", "sucesso")
            else:
                flash("Chamado atualizado no SQLite, mas não foi possível gravar no MongoDB.", "aviso")
        return redirect(url_for("detalhe", chamado_id=chamado_id))

    historico = []
    if mongo_collection is not None:
        try:
            historico = list(mongo_collection.find(
                {"chamado_id": chamado_id}, {"_id": 0}
            ).sort("data", 1))
        except PyMongoError:
            flash("Não foi possível consultar o histórico do MongoDB.", "aviso")
    return render_template("detalhe.html", chamado=chamado, historico=historico,
                           mongo_ok=mongo_collection is not None)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
