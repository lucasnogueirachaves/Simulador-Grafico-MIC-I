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
        estado = self.cpu.get_state()
        subciclo = estado.get("subciclo", 0)
        micros = estado.get("microinstrucoes_executadas", 0)
        texto = f"Subciclo: {subciclo} | Microinstruções: {micros}"
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
                f"{i * 4:04X} {palavra:04X} {texto}" if isinstance(palavra, int) else f"{i * 4:04X} {palavra} {texto}"
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

        if callable(getattr(mem, "carregar_programa", None)):
            mem.carregar_programa(palavras)
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
        try:
            self.cpu.executar_subciclo()
        except NotImplementedError as e:
            self.label_stats.configure(text=str(e))
            return
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