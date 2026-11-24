from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from componentes.controle.memoria_de_controle import MemoriaDeControle
from componentes.cpu import CPU
from montador.checar_erros import ErroDeMontagem
from montador.leitor import separa_linha
from montador.montador import montar

MICROPROGRAMA = Path(__file__).resolve().parent.parent / "assets" / "microprograma.txt"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class Mic1SimulatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        controle = MemoriaDeControle()
        if MICROPROGRAMA.exists() and callable(getattr(controle, "carregar_microprograma_arquivo", None)):
            controle.carregar_microprograma_arquivo(str(MICROPROGRAMA))
        else:
            controle.carregar_microprograma([0x00000000, 0x00000000])

        self.controle = controle
        self.cpu = CPU(controle)
        if callable(getattr(self.cpu, "conectar_controle", None)):
            self.cpu.conectar_controle(controle)

        self.ciclos = 0
        self.instrucoes = 0

        self.title("Simulador MIC-1 - Arquitetura de Computadores")
        self.geometry("1350x850")

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.left_frame = ctk.CTkFrame(self, width=360, corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nsew")

        self.label_editor = ctk.CTkLabel(
            self.left_frame,
            text="Código / Montador MIC-1",
            font=("Arial", 13, "bold"),
        )
        self.label_editor.pack(padx=15, pady=(15, 5), anchor="w")

        self.text_box = ctk.CTkTextbox(
            self.left_frame, height=200, width=330, font=("Consolas", 11)
        )
        self.text_box.pack(padx=15, pady=5)
        self.text_box.insert("0.0", "; Escreva seu código aqui\nLOCO 5\nPUSH\nPOP")

        self.label_maquina = ctk.CTkLabel(
            self.left_frame,
            text="CÓDIGO DE MÁQUINA",
            font=("Arial", 13, "bold"),
        )
        self.label_maquina.pack(padx=15, pady=(10, 5), anchor="w")

        self.machine_code_box = ctk.CTkTextbox(
            self.left_frame,
            height=140,
            width=330,
            font=("Consolas", 11),
            fg_color="#1a1a1a",
        )
        self.machine_code_box.pack(padx=15, pady=5)
        self.machine_code_box.configure(state="disabled")

        self.btn_montar = ctk.CTkButton(
            self.left_frame,
            text="⚙ Montar Código",
            fg_color="#2b6cb0",
            hover_color="#1e4e8c",
            height=32,
            font=("Arial", 12, "bold"),
            command=self.montar_codigo,
        )
        self.btn_montar.pack(padx=15, pady=(6, 4), fill="x")

        self.btn_passo = ctk.CTkButton(
            self.left_frame,
            text="▶ Passo (Fase)",
            fg_color="#1f538d",
            hover_color="#143d6b",
            height=38,
            font=("Arial", 12, "bold"),
            command=self.executar_passo,
        )
        self.btn_passo.pack(padx=15, pady=(10, 8), fill="x")

        self.btn_reiniciar = ctk.CTkButton(
            self.left_frame,
            text="⟳ Reiniciar",
            fg_color="#a83232",
            hover_color="#7a2424",
            height=32,
            font=("Arial", 12, "bold"),
            command=self.reiniciar,
        )
        self.btn_reiniciar.pack(padx=15, pady=5, fill="x")

        self.stats_frame = ctk.CTkFrame(
            self.left_frame, fg_color="#1a1a1a", corner_radius=6
        )
        self.stats_frame.pack(padx=15, pady=(15, 15), fill="x")

        self.label_stats = ctk.CTkLabel(
            self.stats_frame,
            text="Ciclos: 0 | Instruções: 0",
            font=("Consolas", 11, "bold"),
            text_color="#00ffcc",
        )
        self.label_stats.pack(padx=10, pady=8)

        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)

        self.reg_container = ctk.CTkFrame(self.right_frame)
        self.reg_container.grid(row=0, column=0, sticky="nsew", pady=(0, 15))
        self.reg_container.grid_columnconfigure(0, weight=1)

        self.label_regs = ctk.CTkLabel(
            self.reg_container,
            text="REGISTRADORES DO MIC-1",
            font=("Arial", 13, "bold"),
        )
        self.label_regs.pack(padx=15, pady=(10, 5), anchor="w")

        self.regs_grid_frame = ctk.CTkFrame(
            self.reg_container, fg_color="transparent"
        )
        self.regs_grid_frame.pack(padx=15, pady=(0, 10), fill="x")
        self.reg_labels = {}
        self.atualizar_interface_regs()

        self.cache_container = ctk.CTkFrame(self.right_frame)
        self.cache_container.grid(row=1, column=0, sticky="nsew")
        self.cache_container.grid_columnconfigure(0, weight=1)
        self.cache_container.grid_rowconfigure(1, weight=1)

        self.label_cache = ctk.CTkLabel(
            self.cache_container,
            text="MEMÓRIA PRINCIPAL / CACHE (MAPEAMENTO DIRETO)",
            font=("Arial", 13, "bold"),
        )
        self.label_cache.pack(padx=15, pady=(10, 5), anchor="w")

        self.cache_grid_frame = ctk.CTkFrame(
            self.cache_container, fg_color="transparent"
        )
        self.cache_grid_frame.pack(
            padx=15, pady=(0, 15), fill="both", expand=True
        )

        self.cache_labels = []
        self.atualizar_interface_cache()

        self.carregar_programa()

    def atualizar_interface_regs(self):
        for widget in self.regs_grid_frame.winfo_children():
            widget.destroy()

        estado = self.cpu.get_state()
        regs = estado.get("registradores", {})
        col = 0
        row = 0
        for nome, valor in regs.items():
            lbl = ctk.CTkLabel(
                self.regs_grid_frame,
                text=f"{nome}: {hex(valor) if isinstance(valor, int) else valor}",
                font=("Consolas", 12, "bold"),
                fg_color="#262626",
                corner_radius=6,
                height=35,
            )
            lbl.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            self.regs_grid_frame.grid_columnconfigure(col, weight=1)
            self.reg_labels[nome] = lbl

            col += 1
            if col > 2:
                col = 0
                row += 1

    def atualizar_interface_cache(self):
        for widget in self.cache_grid_frame.winfo_children():
            widget.destroy()

        headers = [
            "Índice (#)",
            "Bit V (Validade)",
            "Tag",
            "Bloco / Palavras de Dados",
        ]
        col_weights = [1, 1, 2, 4]

        for col_idx, h_text in enumerate(headers):
            lbl_h = ctk.CTkLabel(
                self.cache_grid_frame,
                text=h_text,
                font=("Arial", 11, "bold"),
                fg_color="#1f538d",
                corner_radius=4,
                height=30,
            )
            lbl_h.grid(row=0, column=col_idx, padx=4, pady=4, sticky="nsew")
            self.cache_grid_frame.grid_columnconfigure(
                col_idx, weight=col_weights[col_idx]
            )

        estado = self.cpu.get_state()
        mem_estado = estado.get("memoria") or {}
        cache_dados = mem_estado.get("cache_dados") or {}
        linhas = (
            cache_dados.get("linhas")
            or mem_estado.get("cache")
            or mem_estado.get("linhas")
            or []
        )

        self.cache_labels = []
        for i in range(8):
            linha = linhas[i] if i < len(linhas) else {}
            if isinstance(linha, dict):
                valido = linha.get("valido", linha.get("v", 0))
                tag = linha.get("tag", "---")
                dados = linha.get(
                    "dado", linha.get("dados", linha.get("bloco", "0x00000000"))
                )
            else:
                valido, tag, dados = 0, "---", "0x00000000"

            if isinstance(dados, int):
                dados_txt = hex(dados)
            elif isinstance(dados, (list, tuple)):
                dados_txt = " ".join(
                    hex(x) if isinstance(x, int) else str(x) for x in dados
                )
            else:
                dados_txt = str(dados)

            tag_txt = hex(tag) if isinstance(tag, int) else str(tag)

            lbl_idx = ctk.CTkLabel(
                self.cache_grid_frame,
                text=f"[{i}]",
                font=("Consolas", 11),
                fg_color="#262626",
                height=28,
            )
            lbl_idx.grid(row=i + 1, column=0, padx=4, pady=2, sticky="nsew")

            lbl_v = ctk.CTkLabel(
                self.cache_grid_frame,
                text=str(int(bool(valido)) if isinstance(valido, bool) else valido),
                font=("Consolas", 11),
                fg_color="#262626",
                height=28,
            )
            lbl_v.grid(row=i + 1, column=1, padx=4, pady=2, sticky="nsew")

            lbl_tag = ctk.CTkLabel(
                self.cache_grid_frame,
                text=tag_txt,
                font=("Consolas", 11),
                fg_color="#262626",
                height=28,
            )
            lbl_tag.grid(row=i + 1, column=2, padx=4, pady=2, sticky="nsew")

            lbl_data = ctk.CTkLabel(
                self.cache_grid_frame,
                text=dados_txt,
                font=("Consolas", 11),
                fg_color="#262626",
                height=28,
            )
            lbl_data.grid(row=i + 1, column=3, padx=4, pady=2, sticky="nsew")

            self.cache_labels.append((lbl_v, lbl_tag, lbl_data))

    def atualizar_valores_cache(self):
        mem_estado = self.cpu.get_state().get("memoria") or {}
        cache_dados = mem_estado.get("cache_dados") or {}
        linhas = cache_dados.get("linhas")
        if not linhas or not self.cache_labels:
            self.atualizar_interface_cache()
            return

        for (lbl_v, lbl_tag, lbl_data), linha in zip(self.cache_labels, linhas):
            valido = bool(linha.get("valido", 0))
            tag = linha.get("tag", "---")
            dado = linha.get("dado", linha.get("dados", 0))
            lbl_v.configure(text="1" if valido else "0")
            lbl_tag.configure(text=str(tag) if valido else "---")
            if isinstance(dado, int):
                lbl_data.configure(text=f"0x{dado:04X}")
            else:
                lbl_data.configure(text=str(dado))

    def atualizar_tela(self):
        self.atualizar_interface_regs()
        self.atualizar_valores_cache()
        texto = f"Ciclos: {self.ciclos} | Instruções: {self.instrucoes}"
        if getattr(self.cpu, "halted", False):
            texto += " | FIM"
        self.label_stats.configure(text=texto)
        self.btn_passo.configure(
            state="disabled" if getattr(self.cpu, "halted", False) else "normal"
        )

    def carregar_programa(self):
        """Monta o texto do editor, carrega na memória e zera a CPU."""
        fonte = self.text_box.get("0.0", "end")
        try:
            resultado = montar(fonte)
        except ErroDeMontagem as erro:
            messagebox.showerror("Erro de montagem", str(erro))
            return
        except Exception as erro:
            messagebox.showerror("Erro ao montar", str(erro))
            return

        if isinstance(resultado, tuple) and len(resultado) >= 1 and isinstance(resultado[0], (list, tuple)):
            palavras = list(resultado[0])
        elif isinstance(resultado, (list, tuple)):
            palavras = list(resultado)
        else:
            palavras = []

        self.cpu.reset()

        mem = getattr(self.cpu, "memoria", None)
        ram_interna = getattr(mem, "memoria", None) if mem is not None else None
        if ram_interna is not None and callable(getattr(ram_interna, "escrever", None)):
            for endereco, palavra in enumerate(palavras):
                if isinstance(palavra, int):
                    ram_interna.escrever(endereco, palavra)

        if callable(getattr(self.cpu, "carregar_programa", None)):
            self.cpu.carregar_programa(palavras)
        else:
            self._carregar_programa_na_cpu(palavras)

        self.ciclos = 0
        self.instrucoes = 0

        textos = []
        for linha in fonte.splitlines():
            try:
                _, instrucao, operando = separa_linha(linha)
                if instrucao:
                    textos.append(f"{instrucao} {operando}" if operando else instrucao)
            except Exception:
                pass

        if textos and len(textos) == len(palavras):
            linhas = [
                f"{i:04X} {palavra:04x} {texto}" if isinstance(palavra, int) else f"{i:04X} {palavra} {texto}"
                for i, (palavra, texto) in enumerate(zip(palavras, textos))
            ]
        else:
            linhas = [
                f"{i * 4:04X} {palavra:08X}" if isinstance(palavra, int) else f"{i * 4:04X} {palavra}"
                for i, palavra in enumerate(palavras)
            ]

        self.machine_code_box.configure(state="normal")
        self.machine_code_box.delete("0.0", "end")
        self.machine_code_box.insert("0.0", "\n".join(linhas))
        self.machine_code_box.configure(state="disabled")
        self.atualizar_tela()

    def montar_codigo(self):
        self.carregar_programa()

    def _carregar_programa_na_cpu(self, palavras):
        mem = getattr(self.cpu, "memoria", None)
        if mem is None:
            return

        for idx, palavra in enumerate(palavras):
            if not isinstance(palavra, int):
                continue
            endereco = idx * 4
            if callable(getattr(mem, "escrever_palavra", None)):
                mem.escrever_palavra(endereco, palavra)
            elif (
                hasattr(self.cpu, "mar")
                and hasattr(self.cpu, "mbr")
                and callable(getattr(mem, "escrever", None))
            ):
                mar_antigo = self.cpu.mar.valor
                mbr_antigo = self.cpu.mbr.valor
                self.cpu.mar.gravar(endereco)
                self.cpu.mbr.gravar(palavra)
                mem.escrever()
                self.cpu.mar.gravar(mar_antigo)
                self.cpu.mbr.gravar(mbr_antigo)

    def executar_passo(self):
        if getattr(self.cpu, "halted", False):
            return
        try:
            self.cpu.executar_subciclo()
        except NotImplementedError as e:
            self.label_stats.configure(text=str(e))
            return
        if getattr(self.cpu, "subciclo", None) == 0:
            self.ciclos += 1
        self.atualizar_tela()

    def reiniciar(self):
        self.cpu.reset()
        self.ciclos = 0
        self.instrucoes = 0
        self.atualizar_tela()


if __name__ == "__main__":
    app = Mic1SimulatorApp()
    app.mainloop()

