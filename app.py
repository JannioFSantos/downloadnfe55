import json
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from xml.etree import ElementTree as ET

APP_TITLE = "Download NF-e 55 - JannioFSantos"

APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR)).resolve()
SOURCE_DIR = Path(__file__).resolve().parent


def resource_bases():
    bases = []
    for base in (APP_DIR, BUNDLE_DIR, SOURCE_DIR):
        base = base.resolve()
        if base not in bases:
            bases.append(base)
    return bases


def find_backend_root():
    for base in resource_bases():
        if (base / "php" / "distribuicao.php").is_file() and (base / "php" / "manifestacao.php").is_file():
            return base
    return APP_DIR


BASE_DIR = find_backend_root()
DIST_SCRIPT = BASE_DIR / "php" / "distribuicao.php"
MANIF_SCRIPT = BASE_DIR / "php" / "manifestacao.php"
VENDOR_AUTOLOAD = BASE_DIR / "vendor" / "autoload.php"


class RuntimeDependencyError(RuntimeError):
    pass


def resolve_php_executable():
    executable_name = "php.exe" if os.name == "nt" else "php"

    for base in resource_bases():
        candidate = base / "runtime" / "php" / executable_name
        if candidate.is_file():
            return str(candidate)

    system_php = shutil.which("php")
    if system_php:
        return system_php

    raise RuntimeDependencyError(
        "Runtime PHP não encontrado.\n\n"
        "Baixe a versão portátil do DownloadNFe55 ou coloque o PHP em runtime\\php.\n"
        "Alternativamente, instale o PHP 8.1 ou superior e deixe o php.exe no PATH do Windows."
    )


class DownloadNFe55App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("940x720")
        self.root.minsize(860, 640)

        self.cnpj = tk.StringVar()
        self.uf = tk.StringVar(value="CE")
        self.certificado = tk.StringVar()
        self.senha = tk.StringVar()
        self.destino = tk.StringVar(value=str(Path.home() / "Downloads" / "NFe55"))
        self.status = tk.StringVar(value="Pronto.")
        self.documentos = {}

        self.build_ui()
        self.carregar_documentos()

    def build_ui(self):
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Download automático de NF-e 55",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            frame,
            text="Distribuição DF-e oficial • Certificado A1 • Controle automático de NSU",
        ).pack(anchor="w", pady=(2, 14))

        form = ttk.Frame(frame)
        form.pack(fill="x")

        self.field(form, "CNPJ", self.cnpj, 0)

        ttk.Label(form, text="UF").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Combobox(
            form,
            textvariable=self.uf,
            state="readonly",
            width=8,
            values="AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split(),
        ).grid(row=1, column=1, sticky="w", pady=5)

        ttk.Label(form, text="Certificado A1").grid(row=2, column=0, sticky="w", pady=5)
        cert_row = ttk.Frame(form)
        cert_row.grid(row=2, column=1, sticky="ew", pady=5)
        ttk.Entry(cert_row, textvariable=self.certificado).pack(side="left", fill="x", expand=True)
        ttk.Button(cert_row, text="Selecionar", command=self.selecionar_certificado).pack(side="left", padx=5)

        self.field(form, "Senha", self.senha, 3, show="•")

        ttk.Label(form, text="Pasta dos XMLs").grid(row=4, column=0, sticky="w", pady=5)
        dest_row = ttk.Frame(form)
        dest_row.grid(row=4, column=1, sticky="ew", pady=5)
        ttk.Entry(dest_row, textvariable=self.destino).pack(side="left", fill="x", expand=True)
        ttk.Button(dest_row, text="Selecionar", command=self.selecionar_pasta).pack(side="left", padx=5)

        form.columnconfigure(1, weight=1)

        botoes = ttk.Frame(frame)
        botoes.pack(fill="x", pady=10)

        self.btn_sync = ttk.Button(botoes, text="1. Sincronizar NF-e", command=self.iniciar_sincronizacao)
        self.btn_sync.pack(side="left")

        ttk.Button(botoes, text="Atualizar lista", command=self.carregar_documentos).pack(side="left", padx=6)

        self.btn_manifestar = ttk.Button(
            botoes,
            text="2. Ciência da Operação",
            command=self.iniciar_manifestacao,
            state="disabled",
        )
        self.btn_manifestar.pack(side="left")

        ttk.Label(frame, textvariable=self.status).pack(anchor="w", pady=(0, 7))

        colunas = ("data", "numero", "emitente", "valor", "situacao")
        self.tree = ttk.Treeview(frame, columns=colunas, show="headings", height=13, selectmode="browse")

        configuracao = [
            ("data", "Emissão", 140),
            ("numero", "NF-e", 90),
            ("emitente", "Emitente", 320),
            ("valor", "Valor", 100),
            ("situacao", "Situação", 170),
        ]

        for coluna, titulo, largura in configuracao:
            self.tree.heading(coluna, text=titulo)
            self.tree.column(coluna, width=largura, anchor="w")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.atualizar_estado_manifestacao)

        ttk.Label(frame, text="Log").pack(anchor="w", pady=(8, 0))
        self.log = tk.Text(frame, height=8, state="disabled", font=("Consolas", 9))
        self.log.pack(fill="x")

    def field(self, parent, label, variable, row, show=None):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        ttk.Entry(parent, textvariable=variable, show=show).grid(row=row, column=1, sticky="ew", pady=5)

    def selecionar_certificado(self):
        path = filedialog.askopenfilename(
            filetypes=[("Certificado A1", "*.pfx *.p12"), ("Todos os arquivos", "*.*")]
        )
        if path:
            self.certificado.set(path)

    def selecionar_pasta(self):
        path = filedialog.askdirectory()
        if path:
            self.destino.set(path)
            self.carregar_documentos()

    def adicionar_log(self, texto):
        self.log.configure(state="normal")
        self.log.insert("end", texto.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def validar(self):
        cnpj = "".join(ch for ch in self.cnpj.get() if ch.isdigit())

        if len(cnpj) != 14:
            raise ValueError("Informe um CNPJ com 14 dígitos.")

        if not Path(self.certificado.get()).is_file():
            raise ValueError("Selecione um certificado A1 válido.")

        if not self.senha.get():
            raise ValueError("Informe a senha do certificado.")

        return cnpj

    def comando_base(self, script, cnpj):
        if not script.is_file():
            raise RuntimeError(f"Script PHP não encontrado: {script}")

        if not VENDOR_AUTOLOAD.is_file():
            raise RuntimeError(
                "Dependências PHP não encontradas. Baixe a versão portátil ou execute composer install."
            )

        return [
            resolve_php_executable(),
            str(script),
            "--cnpj",
            cnpj,
            "--uf",
            self.uf.get(),
            "--cert",
            self.certificado.get(),
            "--password",
            self.senha.get(),
            "--output",
            self.destino.get(),
        ]

    def executar_backend(self, comando):
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        processo = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=flags,
        )

        ultimo = None

        for linha in processo.stdout:
            linha = linha.rstrip()
            self.root.after(0, self.adicionar_log, linha)

            try:
                ultimo = json.loads(linha)
            except json.JSONDecodeError:
                pass

        if processo.wait() != 0:
            raise RuntimeError((ultimo or {}).get("mensagem", "Operação encerrada com erro."))

        return ultimo or {}

    def iniciar_sincronizacao(self):
        try:
            cnpj = self.validar()
        except Exception as exc:
            messagebox.showerror("Validação", str(exc))
            return

        self.btn_sync.configure(state="disabled")
        self.status.set("Consultando Distribuição DF-e...")

        threading.Thread(
            target=self.worker_sincronizacao,
            args=(cnpj,),
            daemon=True,
        ).start()

    def worker_sincronizacao(self, cnpj):
        try:
            Path(self.destino.get()).mkdir(parents=True, exist_ok=True)
            resultado = self.executar_backend(self.comando_base(DIST_SCRIPT, cnpj))

            mensagem = (
                f"Concluído. XML completos: {resultado.get('xml_completos', 0)} | "
                f"Resumos: {resultado.get('resumos', 0)} | "
                f"ultNSU: {resultado.get('ultNSU', '-')}"
            )

            self.root.after(0, self.finalizar_sincronizacao, mensagem, False)

        except Exception as exc:
            self.root.after(0, self.finalizar_sincronizacao, str(exc), True)

    def finalizar_sincronizacao(self, mensagem, erro):
        self.btn_sync.configure(state="normal")
        self.status.set(mensagem)
        self.carregar_documentos()

        if erro:
            messagebox.showerror("NF-e", mensagem)
        else:
            messagebox.showinfo("NF-e", mensagem)

    def ler_documento(self, path):
        try:
            root = ET.parse(path).getroot()

            def valor(tag):
                node = root.find(".//{*}" + tag)
                return (node.text or "").strip() if node is not None else ""

            chave = valor("chNFe")

            if not chave:
                inf = root.find(".//{*}infNFe")
                if inf is not None:
                    chave = inf.attrib.get("Id", "").replace("NFe", "")

            return {
                "path": str(path),
                "chave": chave,
                "data": valor("dhEmi") or valor("dEmi"),
                "numero": valor("nNF"),
                "emitente": valor("xNome"),
                "valor": valor("vNF"),
            }

        except Exception:
            return None

    def carregar_documentos(self):
        if not hasattr(self, "tree"):
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.documentos = {}
        base = Path(self.destino.get())

        for pasta, situacao in [
            ("resumos", "Aguardando manifestação"),
            ("xml", "XML completo"),
        ]:
            diretorio = base / pasta

            if not diretorio.exists():
                continue

            for arquivo in sorted(diretorio.glob("*.xml"), reverse=True):
                dados = self.ler_documento(arquivo)

                if not dados or not dados["chave"]:
                    continue

                iid = self.tree.insert(
                    "",
                    "end",
                    values=(
                        dados["data"][:19],
                        dados["numero"],
                        dados["emitente"],
                        dados["valor"],
                        situacao,
                    ),
                )

                dados["tipo"] = pasta
                self.documentos[iid] = dados

        self.atualizar_estado_manifestacao()

    def atualizar_estado_manifestacao(self, event=None):
        if not hasattr(self, "btn_manifestar"):
            return

        state = "disabled"
        selecao = self.tree.selection() if hasattr(self, "tree") else []

        if selecao:
            documento = self.documentos.get(selecao[0])
            if documento and documento.get("tipo") == "resumos":
                state = "normal"

        self.btn_manifestar.configure(state=state)

    def iniciar_manifestacao(self):
        selecao = self.tree.selection()

        if not selecao:
            messagebox.showwarning("Manifestação", "Selecione uma NF-e.")
            return

        documento = self.documentos.get(selecao[0])

        if not documento or documento["tipo"] != "resumos":
            messagebox.showinfo("Manifestação", "A NF-e selecionada já possui XML completo.")
            return

        confirmar = messagebox.askyesno(
            "Confirmar Ciência da Operação",
            "Registrar Ciência da Operação para esta NF-e?\n\n"
            "Esse é um evento fiscal transmitido à SEFAZ.",
        )

        if not confirmar:
            return

        try:
            cnpj = self.validar()
        except Exception as exc:
            messagebox.showerror("Validação", str(exc))
            return

        self.btn_manifestar.configure(state="disabled")
        self.status.set("Registrando Ciência da Operação...")

        threading.Thread(
            target=self.worker_manifestacao,
            args=(cnpj, documento["chave"]),
            daemon=True,
        ).start()

    def worker_manifestacao(self, cnpj, chave):
        try:
            comando = self.comando_base(MANIF_SCRIPT, cnpj) + ["--chave", chave]
            resultado = self.executar_backend(comando)

            mensagem = (
                f"Manifestação enviada: "
                f"{resultado.get('cStat', '')} {resultado.get('xMotivo', '')}"
            )

            self.root.after(0, self.finalizar_manifestacao, mensagem, False)

        except Exception as exc:
            self.root.after(0, self.finalizar_manifestacao, str(exc), True)

    def finalizar_manifestacao(self, mensagem, erro):
        self.atualizar_estado_manifestacao()
        self.status.set(mensagem)

        if erro:
            messagebox.showerror("Manifestação", mensagem)
        else:
            messagebox.showinfo(
                "Manifestação",
                mensagem
                + "\n\nUse 'Sincronizar NF-e' posteriormente para consultar a disponibilização do XML completo.",
            )


if __name__ == "__main__":
    root = tk.Tk()
    DownloadNFe55App(root)
    root.mainloop()
