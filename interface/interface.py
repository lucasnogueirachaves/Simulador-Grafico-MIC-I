"""Interface didática para a CPU MIC-1.

Execute da raiz do repositório: python -m interface.interface
A janela consulta snapshots da CPU; não reimplementa seus componentes.
"""
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
    """Painel de observação e execução passo a passo do MIC-1."""

    COR_ATIVA = "#237F6D"
    COR_INATIVA = "#303946"
    FASES = ("Busca MIR", "Leitura A/B", "ULA e deslocador", "Escrita / MPC")

    def __init__(self):
        super().__init__()
        controle = MemoriaDeControle()
        if not MICROPROGRAMA.is_file():
            raise FileNotFoundError(f"Microprograma ausente: {MICROPROGRAMA}")
        controle.carregar_microprograma_arquivo(str(MICROPROGRAMA))
        self.controle = controle
        self.cpu = CPU(controle)
        self.executando = False
        self._after_id = None
        self.ciclos = 0
        self.instrucoes = 0
        self.velocidade_ms = 160
        self._palavras_carregadas = []
        self.title("Simulador Gráfico MIC-1")
        self.geometry("1310x830")
        self.minsize(1010, 650)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.left_frame = ctk.CTkScrollableFrame(self, width=340, corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.right_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self._criar_editor_e_controles()
        self._criar_painel_cpu()
        self._criar_painel_registradores()
        self._criar_painel_cache()
        self.protocol("WM_DELETE_WINDOW", self._fechar)
        self.carregar_programa()

    def _titulo(self, parent, texto):
        titulo = ctk.CTkLabel(parent, text=texto, font=("Arial", 14, "bold"))
        titulo.pack(anchor="w", padx=10, pady=(11, 6))
        return titulo

    def _criar_editor_e_controles(self):
        self._titulo(self.left_frame, "Assembly MAC-1")
        self.text_box = ctk.CTkTextbox(self.left_frame, height=210, font=("Consolas", 12))
        self.text_box.pack(fill="x", padx=10, pady=(0, 8))
        self.text_box.insert("0.0", "; Exemplo de programa\nLOCO 5\nPUSH\nPOP")

        linha1 = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        linha1.pack(fill="x", padx=10, pady=4)
        ctk.CTkButton(linha1, text="Montar e carregar", command=self.carregar_programa).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(linha1, text="Reset", width=78, command=self.reiniciar).pack(side="left")

        linha2 = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        linha2.pack(fill="x", padx=10, pady=4)
        self.btn_passo = ctk.CTkButton(linha2, text="Subciclo", command=self.executar_passo)
        self.btn_passo.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.btn_ciclo = ctk.CTkButton(linha2, text="Microinstrução", command=self.executar_ciclo)
        self.btn_ciclo.pack(side="left", expand=True, fill="x")

        linha3 = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        linha3.pack(fill="x", padx=10, pady=4)
        self.btn_run = ctk.CTkButton(linha3, text="Executar", command=self.iniciar_execucao)
        self.btn_run.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.btn_pause = ctk.CTkButton(linha3, text="Pausar", command=self.pausar_execucao, state="disabled")
        self.btn_pause.pack(side="left", expand=True, fill="x")

        self.label_velocidade = ctk.CTkLabel(self.left_frame, text="Intervalo entre subciclos: 160 ms")
        self.label_velocidade.pack(anchor="w", padx=10, pady=(9, 1))
        self.slider_velocidade = ctk.CTkSlider(self.left_frame, from_=40, to=1000,
                                              number_of_steps=48, command=self.alterar_velocidade)
        self.slider_velocidade.pack(fill="x", padx=10, pady=(2, 6))
        self.slider_velocidade.set(self.velocidade_ms)

        self._titulo(self.left_frame, "Código de máquina (endereços de palavra)")
        self.machine_code_box = ctk.CTkTextbox(self.left_frame, height=170, font=("Consolas", 11))
        self.machine_code_box.pack(fill="x", padx=10, pady=(0, 8))
        self.machine_code_box.configure(state="disabled")
        self.label_stats = ctk.CTkLabel(self.left_frame, text="", justify="left", wraplength=325)
        self.label_stats.pack(fill="x", padx=10, pady=6)
        self._titulo(self.left_frame, "Transferências do último subciclo")
        self.label_transferencias = ctk.CTkLabel(self.left_frame, text="Nenhuma operação ainda", justify="left", anchor="w", wraplength=325)
        self.label_transferencias.pack(fill="x", padx=10, pady=(0, 15))

    def _criar_painel_cpu(self):
        self._titulo(self.right_frame, "Via de dados e controle")
        self.cpu_grid = ctk.CTkFrame(self.right_frame)
        self.cpu_grid.pack(fill="x", padx=10, pady=(0, 10))
        for coluna in range(4):
            self.cpu_grid.grid_columnconfigure(coluna, weight=1)
        self.componentes_visuais = {}
        nomes = [
            ("MPC", "MPC"), ("MIR", "MIR"), ("CONTROLE", "MEMORIA_CONTROLE"), ("AMUX", "AMUX"),
            ("LATCH A", "LATCH_A"), ("LATCH B", "LATCH_B"), ("ULA", "ULA"), ("DESLOCADOR", "DESLOCADOR"),
            ("BARR. A", "BARRAMENTO_A"), ("BARR. B", "BARRAMENTO_B"), ("BARR. C", "BARRAMENTO_C"), ("MAR", "MAR"),
            ("MBR", "MBR"), ("CACHE INST.", "CACHE_INSTRUCOES"), ("CACHE DADOS", "CACHE_DADOS"), ("RAM", "RAM"),
        ]
        for i, (texto, chave) in enumerate(nomes):
            lbl = ctk.CTkLabel(self.cpu_grid, text=texto, fg_color=self.COR_INATIVA,
                               corner_radius=6, height=37, font=("Arial", 11, "bold"))
            lbl.grid(row=i // 4, column=i % 4, padx=5, pady=5, sticky="ew")
            self.componentes_visuais[chave] = lbl
        self.label_fase = ctk.CTkLabel(self.right_frame, text="", font=("Arial", 12))
        self.label_fase.pack(anchor="w", padx=12, pady=(0, 8))
        self.label_sinais = ctk.CTkLabel(self.right_frame, text="", justify="left", anchor="w", wraplength=820)
        self.label_sinais.pack(fill="x", padx=12, pady=(0, 10))

    def _criar_painel_registradores(self):
        self._titulo(self.right_frame, "Registradores (hexadecimal)")
        self.regs_grid_frame = ctk.CTkFrame(self.right_frame)
        self.regs_grid_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.reg_labels = {}
        for coluna in range(4):
            self.regs_grid_frame.grid_columnconfigure(coluna, weight=1)
        for indice, nome in enumerate(("PC", "AC", "SP", "IR", "TIR", "0", "+1", "-1", "AMASK", "SMASK", "A", "B", "C", "D", "E", "F")):
            celula = ctk.CTkFrame(self.regs_grid_frame)
            celula.grid(row=indice // 4, column=indice % 4, sticky="ew", padx=4, pady=4)
            ctk.CTkLabel(celula, text=nome, font=("Arial", 10, "bold")).pack(anchor="w", padx=8)
            lbl = ctk.CTkLabel(celula, text="0000", font=("Consolas", 14))
            lbl.pack(anchor="w", padx=8, pady=(0, 4))
            self.reg_labels[nome] = lbl
        rodape = ctk.CTkFrame(self.regs_grid_frame, fg_color="transparent")
        rodape.grid(row=4, column=0, columnspan=4, sticky="ew", padx=4, pady=8)
        self.label_barramentos = ctk.CTkLabel(rodape, text="", font=("Consolas", 11), justify="left")
        self.label_barramentos.pack(anchor="w", padx=5)

    def _criar_painel_cache(self):
        self._titulo(self.right_frame, "Caches de mapeamento direto")
        self.cache_container = ctk.CTkFrame(self.right_frame)
        self.cache_container.pack(fill="x", padx=10, pady=(0, 14))
        self.cache_container.grid_columnconfigure(0, weight=1)
        self.cache_container.grid_columnconfigure(1, weight=1)
        self.cache_labels = {}
        self.cache_stats_labels = {}
        for coluna, (chave, titulo) in enumerate((("cache_instrucoes", "Cache de instruções"),
                                                  ("cache_dados", "Cache de dados"))):
            painel = ctk.CTkFrame(self.cache_container)
            painel.grid(row=0, column=coluna, sticky="nsew", padx=7, pady=7)
            ctk.CTkLabel(painel, text=titulo, font=("Arial", 13, "bold")).pack(pady=(7, 2))
            stats = ctk.CTkLabel(painel, text="Hits: 0 | Misses: 0", font=("Arial", 10))
            stats.pack()
            self.cache_stats_labels[chave] = stats
            grid = ctk.CTkFrame(painel, fg_color="transparent")
            grid.pack(fill="x", padx=8, pady=(5, 9))
            for j, cab in enumerate(("Linha", "V", "Tag", "Dado")):
                grid.grid_columnconfigure(j, weight=1)
                ctk.CTkLabel(grid, text=cab, font=("Arial", 10, "bold")).grid(row=0, column=j, padx=3)
            self.cache_labels[chave] = []
            num_linhas = getattr(getattr(self.cpu.memoria, chave), "num_linhas", 8)
            for i in range(num_linhas):
                ctk.CTkLabel(grid, text=str(i)).grid(row=i + 1, column=0)
                dados = []
                for j in range(1, 4):
                    lbl = ctk.CTkLabel(grid, text="---", font=("Consolas", 11))
                    lbl.grid(row=i + 1, column=j, padx=4, pady=1, sticky="ew")
                    dados.append(lbl)
                self.cache_labels[chave].append(tuple(dados))
        self.label_ultima_memoria = ctk.CTkLabel(self.cache_container, text="Último acesso: nenhum", justify="left")
        self.label_ultima_memoria.grid(row=1, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 7))

    def alterar_velocidade(self, valor):
        self.velocidade_ms = int(valor)
        self.label_velocidade.configure(text=f"Intervalo entre subciclos: {self.velocidade_ms} ms")

    def _parar_tarefa(self):
        self.executando = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None

    def pausar_execucao(self):
        self._parar_tarefa()
        self.atualizar_tela()

    def iniciar_execucao(self):
        if self.executando or self.cpu.halted:
            return
        self.executando = True
        self.atualizar_tela()
        self._tick_execucao()

    def _tick_execucao(self):
        self._after_id = None
        if not self.executando:
            return
        try:
            self.cpu.executar_subciclo()
            self.ciclos += 1
        except Exception as erro:
            self._parar_tarefa()
            messagebox.showerror("Falha durante a execução", str(erro))
            self.atualizar_tela()
            return
        if self.cpu.halted:
            self._parar_tarefa()
        self.atualizar_tela()
        if self.executando:
            self._after_id = self.after(self.velocidade_ms, self._tick_execucao)

    def executar_passo(self):
        if self.executando or self.cpu.halted:
            return
        try:
            self.cpu.executar_subciclo()
            self.ciclos += 1
        except Exception as erro:
            messagebox.showerror("Falha durante a execução", str(erro))
            return
        self.atualizar_tela()

    def executar_ciclo(self):
        if self.executando or self.cpu.halted:
            return
        try:
            antes = self.cpu.subciclo
            self.cpu.executar_ciclo()
            self.ciclos += 4 - antes
        except Exception as erro:
            messagebox.showerror("Falha durante a execução", str(erro))
            return
        self.atualizar_tela()

    def carregar_programa(self):
        """Monta, troca a RAM e reinicia a execução apenas após montagem válida."""
        self._parar_tarefa()
        fonte = self.text_box.get("0.0", "end")
        try:
            resultado = montar(fonte)
            palavras = list(resultado[0])
            self.cpu.carregar_programa(palavras)
        except (ErroDeMontagem, ValueError, IndexError) as erro:
            messagebox.showerror("Erro ao montar/carregar", str(erro))
            self.atualizar_tela()
            return
        except Exception as erro:
            messagebox.showerror("Falha ao carregar programa", str(erro))
            self.atualizar_tela()
            return
        self._palavras_carregadas = palavras
        # A pilha inicia fora da região ocupada pelo programa de demonstração.
        self.cpu.registradores.gravar(2, max(100, len(palavras) + 16))
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
        linhas = []
        for i, palavra in enumerate(palavras):
            comentario = f"  {textos[i]}" if len(textos) == len(palavras) else ""
            linhas.append(f"{i:04X}: {palavra:04X}{comentario}")
        self.machine_code_box.configure(state="normal")
        self.machine_code_box.delete("0.0", "end")
        self.machine_code_box.insert("0.0", "\n".join(linhas))
        self.machine_code_box.configure(state="disabled")
        self.atualizar_tela()

    def montar_codigo(self):
        self.carregar_programa()

    def reiniciar(self):
        """Volta à primeira microinstrução, sem perder o código da RAM."""
        self._parar_tarefa()
        self.cpu.reset(limpar_memoria=False)
        self.cpu.registradores.gravar(2, max(100, len(self._palavras_carregadas) + 16))
        self.ciclos = 0
        self.instrucoes = 0
        self.atualizar_tela()

    def atualizar_interface_regs(self, estado=None):
        estado = self.cpu.get_state() if estado is None else estado
        for nome, lbl in self.reg_labels.items():
            lbl.configure(text=f"{estado['registradores'].get(nome, 0) & 0xFFFF:04X}")
        self.label_barramentos.configure(
            text=(f"MAR={estado['mar']:03X}  MBR={estado['mbr']:04X}  "
                  f"A={estado['barramento_a']:04X}  B={estado['barramento_b']:04X}\n"
                  f"ULA={estado['resultado_ula']:04X}  DESL={estado['resultado_deslocador']:04X}  "
                  f"N={estado['flag_n']}  Z={estado['flag_z']}")
        )

    def atualizar_interface_cache(self, estado=None):
        estado = self.cpu.get_state() if estado is None else estado
        memoria = estado["memoria"]
        for chave, labels in self.cache_labels.items():
            cache = memoria[chave]
            self.cache_stats_labels[chave].configure(text=f"Hits: {cache['hits']} | Misses: {cache['misses']}")
            for (lbl_valido, lbl_tag, lbl_dado), linha in zip(labels, cache["linhas"]):
                valido = bool(linha["valido"])
                lbl_valido.configure(text="1" if valido else "0")
                lbl_tag.configure(text=str(linha["tag"]) if valido else "---")
                lbl_dado.configure(text=f"{linha['dado']:04X}" if valido else "----")
        op = memoria["ultima_operacao"]
        if op:
            texto = f"Último acesso: {op['tipo']} em {op['endereco']:03X}"
            if "cache" in op:
                texto += f" | {op['cache']} ({op['resultado']})"
        else:
            texto = "Último acesso: nenhum"
        self.label_ultima_memoria.configure(text=texto)

    def atualizar_valores_cache(self):
        """Compatibilidade com a interface antiga."""
        self.atualizar_interface_cache()

    def atualizar_tela(self):
        estado = self.cpu.get_state()
        self.atualizar_interface_regs(estado)
        self.atualizar_interface_cache(estado)
        ativos = set(estado["componentes_ativos"])
        if "RD" in ativos or "WR" in ativos:
            ativos.add("RAM")
        for nome, lbl in self.componentes_visuais.items():
            lbl.configure(fg_color=self.COR_ATIVA if nome in ativos else self.COR_INATIVA)
        fase = estado["ultima_etapa_executada"]
        ultimo = "Nenhuma" if fase is None else self.FASES[fase]
        self.label_fase.configure(text=f"Último subciclo: {ultimo} | Próximo: {self.FASES[estado['subciclo']]}")
        sinais = estado["sinais"] or {}
        self.label_sinais.configure(text="MIR: %08X  MPC: %02X | %s" % (
            estado["mir"], estado["mpc"],
            "  ".join(f"{chave}={valor}" for chave, valor in sinais.items()) if sinais else "Sem MIR carregado"
        ))
        self.label_transferencias.configure(text="\n".join(estado["transferencias"]) or "Nenhuma operação ainda")
        self.label_stats.configure(text=(
            f"Subciclo seguinte: {estado['subciclo']} | "
            f"Microinstruções concluídas: {estado['microinstrucoes_executadas']}\n"
            f"Passos executados: {self.ciclos}" + (" | FIM" if estado["halted"] else "")
        ))
        pode_passo = not estado["halted"] and not self.executando
        self.btn_passo.configure(state="normal" if pode_passo else "disabled")
        self.btn_ciclo.configure(state="normal" if pode_passo else "disabled")
        self.btn_run.configure(state="normal" if pode_passo else "disabled")
        self.btn_pause.configure(state="normal" if self.executando else "disabled")

    def _fechar(self):
        self._parar_tarefa()
        self.destroy()


if __name__ == "__main__":
    app = Mic1SimulatorApp()
    app.mainloop()
