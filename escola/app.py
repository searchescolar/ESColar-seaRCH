from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")

os.makedirs(app.instance_path, exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(app.instance_path, "escola.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


with app.app_context():
    db.create_all()


def usuario_logado(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Entre na sua conta para acessar essa página.", "aviso")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# Os editais ficam no código, sem vínculo com o banco de dados.
EDITAIS = [
    {
        "id": 1,
        "titulo": "PROCESSO DE SELEÇÃO DE DISCENTES E SERVIDORES PARA INTERCÂMBIO INTERNACIONAL NO CANADÁ 2026",
        "descricao": "Resultado da apuração.",
        "ano": 2026,
        "arquivo": "editais/edital1.pdf",
    },
    {
        "id": 2,
        "titulo": "SELEÇÃO INTERNA BANDA DO IFAP CAMPUS MACAPÁ",
        "descricao": "Abertura das inscrições no processo de seleção para provimento de vagas para as funções de coordenador da banda.",
        "ano": 2026,
        "arquivo": "editais/edital2.pdf",
    },
    {
        "id": 3,
        "titulo": "PROCESSO SELETIVO DISCENTE PARA INGRESSO NOS CURSOS TÉCNICOS DE NÍVEL MÉDIO",
        "descricao": "Processo Seletivo Discente (PSD) para preenchimento de vagas para ingresso nos cursos técnicos de nível médio na forma integrada/integral e modalidade presencial.",
        "ano": 2026,
        "arquivo": "editais/edital3.pdf",
    },
]


@app.route("/")
def inicio():
    return render_template("Index.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        if not nome or not email or not senha:
            flash("Preencha todos os campos.", "erro")
        elif len(senha) < 8:
            flash("A senha precisa ter pelo menos 8 caracteres.", "erro")
        elif senha != confirmar_senha:
            flash("As senhas não coincidem.", "erro")
        elif Usuario.query.filter_by(email=email).first():
            flash("Já existe uma conta com esse e-mail.", "erro")
        else:
            usuario = Usuario(nome=nome, email=email)
            usuario.definir_senha(senha)
            db.session.add(usuario)
            db.session.commit()
            flash("Conta criada! Agora você pode entrar.", "sucesso")
            return redirect(url_for("login"))

    return render_template("Cadastro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and usuario.verificar_senha(senha):
            session.clear()
            session["usuario_id"] = usuario.id
            session["usuario_nome"] = usuario.nome
            return redirect(url_for("inicio"))

        flash("E-mail ou senha incorretos.", "erro")

    return render_template("Login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("inicio"))


@app.route("/sobre")
def sobre():
    return render_template("Sobre.html")


@app.route("/editais")
def editais():
    pesquisa = request.args.get("pesquisa", "").strip().casefold()

    if pesquisa:
        resultados = [
            edital for edital in EDITAIS
            if pesquisa in edital["titulo"].casefold()
            or pesquisa in edital["descricao"].casefold()
        ]
    else:
        resultados = EDITAIS

    return render_template(
        "Editais.html",
        editais=resultados,
        pesquisa=request.args.get("pesquisa", "").strip()
    )

@app.route("/faq")
def faq():
    return render_template("FAQ.html")


@app.route("/suporte")
def suporte():
    return render_template("Suporte.html")


if __name__ == "__main__":
    app.run(debug=True)
