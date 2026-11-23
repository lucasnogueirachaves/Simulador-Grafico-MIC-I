import re
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from componentes.controle.memoria_de_controle import MemoriaDeControle
from componentes.cpu import CPU
from montador.checar_erros import ErroDeMontagem
from montador.leitor import separa_linha
from montador.montador import montar

MICROPROGRAMA = Path(__file__).resolve().parent.parent / "assets" / "microprograma.txt"

FASES = ["Busca da microinstrução", "Leitura dos operandos", "ULA e deslocador", "Escrita e próximo MPC"]
COR_CELULA = "#262626"
COR_DESTAQUE = "#14574a"        # tom escuro do verde-água já usado nos contadores
JANELA_MEMORIA = 64             # endereços mostrados no painel de memória
# velocidade -> (intervalo em ms, subciclos por intervalo)
VELOCIDADES = {1: (800, 1), 2: (400, 1), 3: (200, 1), 4: (100, 1), 5: (50, 1),
               6: (25, 1), 7: (10, 1), 8: (10, 4), 9: (10, 16), 10: (10, 64)}


def carregar_descricoes():
    """Lê o texto de cada microinstrução (comentário do microprograma.txt)."""
    descricoes = []
    for linha in open(MICROPROGRAMA, encoding="utf-8"):
        codigo, _, comentario = linha.partition("#")
        if codigo.strip():
            descricoes.append(re.sub(r"^\[\d+\]\s*", "", comentario.strip()))
    return descricoes


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class Mic1SimulatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # núcleo do simulador
        controle = MemoriaDeControle()
        controle.carregar_microprograma_arquivo(str(MICROPROGRAMA))
        self.cpu = CPU(controle)
        self.descricoes = carregar_descricoes()
        self.ciclos = 0
        self.instrucoes = 0
        self.variaveis = {}
        self.executando = False
        self._after_id = None
        self.fase_executada = None      # último subciclo executado (0 a 3)
        self.micro_atual = None         # endereço da última microinstrução buscada
        self._zerar_destaques()

        self.title("Simulador MIC-1 - Arquitetura de Computadores")
        self.geometry("1350 = 850" if False else "1350x900")

        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        
        self.left_frame = ctk.CTkFrame(self, width=360, corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        
    
        self.label_editor = ctk.CTkLabel(self.left_frame, text="Código / Montador MIC-1", font=("Arial", 13, "bold"))
        self.label_editor.pack(padx=15, pady=(15, 5), anchor="w")

        self.text_box = ctk.CTkTextbox(self.left_frame, height=200, width=330, font=("Consolas", 11))
        self.text_box.pack(padx=15, pady=5)
        self.text_box.insert("0.0", "; Escreva seu código aqui\nLOCO 7\nSTOD x\nADDD x")

        
        self.label_机器 = ctk.CTkLabel(self.left_frame, text="CÓDIGO DE MÁQUINA", font=("Arial", 13, "bold"))
        self.label_机器.pack(padx=15, pady=(10, 5), anchor="w")

        self.machine_code_box = ctk.CTkTextbox(self.left_frame, height=140, width=330, font=("Consolas", 11), fg_color="#1a1a1a")
        self.machine_code_box.pack(padx=15, pady=5)
        self.machine_code_box.configure(state="disabled")

        
        self.btn_passo = ctk.CTkButton(self.left_frame, text="▶  Passo (Fase)", fg_color="#1f538d", hover_color="#143d6b", height=38, font=("Arial", 12, "bold"), command=self.executar_passo)
        self.btn_passo.pack(padx=15, pady=(15, 8), fill="x")

        self.step_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.step_frame.pack(padx=15, pady=(0, 8), fill="x")
        self.step_frame.grid_columnconfigure(0, weight=1)
        self.step_frame.grid_columnconfigure(1, weight=1)

        self.btn_micro = ctk.CTkButton(self.step_frame, text="▶  Micro", fg_color="#1f538d", hover_color="#143d6b", height=38, font=("Arial", 12, "bold"), command=self.executar_microinstrucao)
        self.btn_micro.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.btn_instr = ctk.CTkButton(self.step_frame, text="▶  Instrução", fg_color="#1f538d", hover_color="#143d6b", height=38, font=("Arial", 12, "bold"), command=self.executar_instrucao)
        self.btn_instr.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        self.btn_executar = ctk.CTkButton(self.left_frame, text="▶  Executar", fg_color="#2b7a4b", hover_color="#1f5a37", height=38, font=("Arial", 12, "bold"), command=self.alternar_execucao)
        self.btn_executar.pack(padx=15, pady=(0, 8), fill="x")

        self.speed_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.speed_frame.pack(padx=15, pady=(0, 8), fill="x")
        self.label_velocidade = ctk.CTkLabel(self.speed_frame, text="Velocidade: 5", font=("Consolas", 11, "bold"))
        self.label_velocidade.pack(side="left")
        self.slider_velocidade = ctk.CTkSlider(self.speed_frame, from_=1, to=10, number_of_steps=9, command=self.mudou_velocidade)
        self.slider_velocidade.set(5)
        self.slider_velocidade.pack(side="right", fill="x", expand=True, padx=(10, 0))

        self.btn_reiniciar = ctk.CTkButton(self.left_frame, text="⟳  Reiniciar", fg_color="#a83232", hover_color="#7a2424", height=32, font=("Arial", 12, "bold"), command=self.reiniciar)
        self.btn_reiniciar.pack(padx=15, pady=5, fill="x")

        
        self.stats_frame = ctk.CTkFrame(self.left_frame, fg_color="#1a1a1a", corner_radius=6)
        self.stats_frame.pack(padx=15, pady=(15, 15), fill="x")
        
        self.label_stats = ctk.CTkLabel(self.stats_frame, text="Ciclos: 0  |  Instruções: 0", font=("Consolas", 11, "bold"), text_color="#00ffcc")
        self.label_stats.pack(padx=10, pady=8)

        
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(2, weight=1)

        
        self.reg_container = ctk.CTkFrame(self.right_frame)
        self.reg_container.grid(row=0, column=0, sticky="nsew", pady=(0, 15))
        self.reg_container.grid_columnconfigure(0, weight=1)

        self.label_regs = ctk.CTkLabel(self.reg_container, text="REGISTRADORES DO MIC-1", font=("Arial", 13, "bold"))
        self.label_regs.pack(padx=15, pady=(10, 5), anchor="w")

        self.regs_grid_frame = ctk.CTkFrame(self.reg_container, fg_color="transparent")
        self.regs_grid_frame.pack(padx=15, pady=(0, 10), fill="x")
        self.reg_labels = {}
        self.atualizar_interface_regs()

        
        self.controle_container = ctk.CTkFrame(self.right_frame)
        self.controle_container.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        self.controle_container.grid_columnconfigure(0, weight=1)

        self.label_controle = ctk.CTkLabel(self.controle_container, text="UNIDADE DE CONTROLE", font=("Arial", 13, "bold"))
        self.label_controle.pack(padx=15, pady=(10, 5), anchor="w")

        self.controle_grid_frame = ctk.CTkFrame(self.controle_container, fg_color="transparent")
        self.controle_grid_frame.pack(padx=15, pady=(0, 10), fill="x")
        self.criar_painel_controle()

        
        self.cache_container = ctk.CTkFrame(self.right_frame)
        self.cache_container.grid(row=2, column=0, sticky="nsew")
        self.cache_container.grid_columnconfigure(0, weight=1)
        self.cache_container.grid_rowconfigure(1, weight=1)

        self.label_cache = ctk.CTkLabel(self.cache_container, text="MEMÓRIA PRINCIPAL / CACHE (MAPEAMENTO DIRETO)", font=("Arial", 13, "bold"))
        self.label_cache.pack(padx=15, pady=(10, 5), anchor="w")

        self.memory_box = ctk.CTkTextbox(self.cache_container, width=300, font=("Consolas", 11), fg_color="#1a1a1a")
        self.memory_box.pack(side="right", padx=(0, 15), pady=(0, 15), fill="y")
        self.memory_box.tag_config("mud", background=COR_DESTAQUE)
        self.memory_box.tag_config("sp", background="#7a5c00")
        self.memory_box.tag_config("pc", background="#1f538d")
        self.memory_box.configure(state="disabled")

        self.cache_grid_frame = ctk.CTkFrame(self.cache_container, fg_color="transparent")
        self.cache_grid_frame.pack(side="left", padx=15, pady=(0, 15), fill="both", expand=True)
        
        self.cache_labels = []
        self.atualizar_interface_cache()

        # monta o programa do editor e preenche a tela
        self.carregar_programa()

    def _zerar_destaques(self):
        """Esquece o estado anterior: o próximo desenho não destaca nada."""
        self.regs_anteriores = None
        self.cache_anterior = None
        self.mem_anterior = None
        self.pc_anterior = None

    def atualizar_interface_regs(self, estado=None):
        if estado is None:
            estado = self.cpu.get_state()
        regs = estado["registradores"]

        if not self.reg_labels:                     # primeira vez: cria os labels
            col = 0
            row = 0
            for nome, valor in regs.items():
                lbl = ctk.CTkLabel(
                    self.regs_grid_frame, 
                    text=f"{nome}: {hex(valor) if isinstance(valor, int) else valor}", 
                    font=("Consolas", 12, "bold"), 
                    fg_color=COR_CELULA, 
                    corner_radius=6, 
                    height=35
                )
                lbl.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
                self.regs_grid_frame.grid_columnconfigure(col, weight=1)
                self.reg_labels[nome] = lbl
                
                col += 1
                if col > 2: 
                    col = 0
                    row += 1
            self.regs_anteriores = dict(regs)
            return

        for nome, valor in regs.items():            # depois: só atualiza e destaca
            mudou = self.regs_anteriores is not None and self.regs_anteriores.get(nome) != valor
            self.reg_labels[nome].configure(
                text=f"{nome}: {hex(valor) if isinstance(valor, int) else valor}",
                fg_color=COR_DESTAQUE if mudou else COR_CELULA)
        self.regs_anteriores = dict(regs)

    def criar_painel_controle(self):
        estilo = dict(font=("Consolas", 12, "bold"), fg_color=COR_CELULA, corner_radius=6, height=35)
        for col in range(4):
            self.controle_grid_frame.grid_columnconfigure(col, weight=1)

        self.lbl_mpc = ctk.CTkLabel(self.controle_grid_frame, text="MPC: 0x0", **estilo)
        self.lbl_mpc.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
        self.lbl_mir = ctk.CTkLabel(self.controle_grid_frame, text="MIR: 0x00000000", **estilo)
        self.lbl_mir.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")
        self.lbl_n = ctk.CTkLabel(self.controle_grid_frame, text="N: 0", **estilo)
        self.lbl_n.grid(row=0, column=2, padx=6, pady=6, sticky="nsew")
        self.lbl_z = ctk.CTkLabel(self.controle_grid_frame, text="Z: 0", **estilo)
        self.lbl_z.grid(row=0, column=3, padx=6, pady=6, sticky="nsew")

        self.lbl_fase = ctk.CTkLabel(self.controle_grid_frame, text="Fase: ---", **estilo)
        self.lbl_fase.grid(row=1, column=0, columnspan=2, padx=6, pady=6, sticky="nsew")
        self.lbl_micro = ctk.CTkLabel(self.controle_grid_frame, text="Microinstrução: ---", **estilo)
        self.lbl_micro.grid(row=1, column=2, columnspan=2, padx=6, pady=6, sticky="nsew")

    def atualizar_painel_controle(self, estado):
        self.lbl_mpc.configure(text=f"MPC: {hex(estado['mpc'])}")
        self.lbl_mir.configure(text=f"MIR: 0x{estado['mir']:08X}")
        self.lbl_n.configure(text=f"N: {estado['flag_n']}")
        self.lbl_z.configure(text=f"Z: {estado['flag_z']}")

        if self.fase_executada is None:
            self.lbl_fase.configure(text="Fase: ---")
        else:
            self.lbl_fase.configure(text=f"Fase {self.fase_executada + 1}/4: {FASES[self.fase_executada]}")

        if self.micro_atual is None:
            self.lbl_micro.configure(text="Microinstrução: ---")
        else:
            texto = self.descricoes[self.micro_atual] if self.micro_atual < len(self.descricoes) else "(sem descrição)"
            self.lbl_micro.configure(text=f"[{self.micro_atual}] {texto}")

    def atualizar_interface_cache(self):
        headers = ["Índice (#)", "Bit V (Validade)", "Tag", "Bloco / Palavras de Dados"]
        col_weights = [1, 1, 2, 4]

        for col_idx, h_text in enumerate(headers):
            lbl_h = ctk.CTkLabel(self.cache_grid_frame, text=h_text, font=("Arial", 11, "bold"), fg_color="#1f538d", corner_radius=4, height=30)
            lbl_h.grid(row=0, column=col_idx, padx=4, pady=4, sticky="nsew")
            self.cache_grid_frame.grid_columnconfigure(col_idx, weight=col_weights[col_idx])

        self.cache_labels = []
        for i in range(8):
            lbl_idx = ctk.CTkLabel(self.cache_grid_frame, text=f"[{i}]", font=("Consolas", 11), fg_color=COR_CELULA, height=28)
            lbl_idx.grid(row=i+1, column=0, padx=4, pady=2, sticky="nsew")

            lbl_v = ctk.CTkLabel(self.cache_grid_frame, text="0", font=("Consolas", 11), fg_color=COR_CELULA, height=28)
            lbl_v.grid(row=i+1, column=1, padx=4, pady=2, sticky="nsew")

            lbl_tag = ctk.CTkLabel(self.cache_grid_frame, text="---", font=("Consolas", 11), fg_color=COR_CELULA, height=28)
            lbl_tag.grid(row=i+1, column=2, padx=4, pady=2, sticky="nsew")

            lbl_data = ctk.CTkLabel(self.cache_grid_frame, text="0x0000", font=("Consolas", 11), fg_color=COR_CELULA, height=28)
            lbl_data.grid(row=i+1, column=3, padx=4, pady=2, sticky="nsew")

            self.cache_labels.append((lbl_v, lbl_tag, lbl_data))

    def atualizar_valores_cache(self, estado):
        linhas = estado["memoria"]["cache_dados"]["linhas"]
        for i, ((lbl_v, lbl_tag, lbl_data), linha) in enumerate(zip(self.cache_labels, linhas)):
            mudou = self.cache_anterior is not None and linha != self.cache_anterior[i]
            cor = COR_DESTAQUE if mudou else COR_CELULA
            lbl_v.configure(text="1" if linha["valido"] else "0", fg_color=cor)
            lbl_tag.configure(text=str(linha["tag"]) if linha["valido"] else "---", fg_color=cor)
            lbl_data.configure(text=f"0x{linha['dado']:04X}", fg_color=cor)
        self.cache_anterior = [dict(linha) for linha in linhas]

    def atualizar_memoria(self, estado):
        dados = list(self.cpu.memoria.memoria.dados)
        pc = estado["registradores"]["PC"]
        sp = estado["registradores"]["SP"] & 0x0FFF
        nomes = {endereco: nome for nome, endereco in self.variaveis.items()}

        enderecos = list(range(JANELA_MEMORIA))
        if sp >= JANELA_MEMORIA:                    # pilha fora da janela: mostra o topo dela
            enderecos += [None] + list(range(sp, min(sp + 8, len(dados))))

        linhas, tags = ["End.   Valor  Marca"], []
        for endereco in enderecos:
            if endereco is None:
                linhas.append("--- pilha ---")
                continue
            numero = len(linhas) + 1                # linha 1 é o cabeçalho
            mudou = self.mem_anterior is not None and dados[endereco] != self.mem_anterior[endereco]
            marcas = []
            if endereco == pc:
                marcas.append("◄ PC")
            if endereco == sp:
                marcas.append("◄ SP")
            if endereco in nomes:
                marcas.append(nomes[endereco])
            if endereco == pc:
                tags.append(("pc", numero))
            elif mudou:
                tags.append(("mud", numero))
            elif endereco == sp:
                tags.append(("sp", numero))
            linhas.append(f"{endereco:04X}   {dados[endereco]:04X}   {' '.join(marcas)}".rstrip())

        self.memory_box.configure(state="normal")
        self.memory_box.delete("0.0", "end")
        self.memory_box.insert("0.0", "\n".join(linhas))
        for tag, linha in tags:
            self.memory_box.tag_add(tag, f"{linha}.0", f"{linha}.end")
        if pc != self.pc_anterior and pc < JANELA_MEMORIA:
            self.memory_box.see(f"{pc + 2}.0")      # acompanha o PC (linha 1 é o cabeçalho)
        self.memory_box.configure(state="disabled")
        self.mem_anterior = dados
        self.pc_anterior = pc

    def atualizar_botoes(self):
        parado = self.cpu.halted
        bloqueia_passos = parado or self.executando
        for botao in (self.btn_passo, self.btn_micro, self.btn_instr):
            botao.configure(state="disabled" if bloqueia_passos else "normal")
        self.btn_executar.configure(state="disabled" if parado else "normal")

    def atualizar_tela(self):
        estado = self.cpu.get_state()
        self.atualizar_interface_regs(estado)
        self.atualizar_painel_controle(estado)
        self.atualizar_valores_cache(estado)
        self.atualizar_memoria(estado)
        texto = f"Ciclos: {self.ciclos}  |  Instruções: {self.instrucoes}"
        if self.cpu.halted:
            texto += "  |  FIM"
        self.label_stats.configure(text=texto)
        self.atualizar_botoes()

    def carregar_programa(self):
        """Monta o texto do editor, carrega na memória e zera a CPU."""
        fonte = self.text_box.get("0.0", "end")
        try:
            palavras, _, variaveis = montar(fonte)
        except ErroDeMontagem as erro:
            messagebox.showerror("Erro de montagem", str(erro))
            return

        self.cpu.reset()
        self.cpu.carregar_programa(palavras)
        self.variaveis = variaveis
        self.ciclos = 0
        self.instrucoes = 0
        self.fase_executada = None
        self.micro_atual = None
        self._zerar_destaques()

        # texto de cada instrução, na mesma ordem das palavras montadas
        textos = []
        for linha in fonte.splitlines():
            _, instrucao, operando = separa_linha(linha)
            if instrucao:
                textos.append(f"{instrucao} {operando}" if operando else instrucao)

        linhas = [f"{i:04X}  {palavra:04x}  {texto}"
                  for i, (palavra, texto) in enumerate(zip(palavras, textos))]
        self.machine_code_box.configure(state="normal")
        self.machine_code_box.delete("0.0", "end")
        self.machine_code_box.insert("0.0", "\n".join(linhas))
        self.machine_code_box.configure(state="disabled")

        self.atualizar_tela()

    def avancar_subciclo(self):
        """Executa um subciclo e atualiza os contadores e a fase mostrada."""
        if self.cpu.subciclo == 0:
            self.micro_atual = self.cpu.mpc         # microinstrução que vai ser buscada
        self.fase_executada = self.cpu.subciclo
        self.cpu.executar_subciclo()
        if self.cpu.subciclo == 0:                  # fechou uma microinstrução
            self.ciclos += 1
            if self.cpu.mpc == 0:                   # voltou à busca: terminou uma instrução
                self.instrucoes += 1

    def executar_passo(self):
        if self.cpu.halted:
            return
        self.avancar_subciclo()
        self.atualizar_tela()

    def executar_microinstrucao(self):
        if self.cpu.halted:
            return
        while True:
            self.avancar_subciclo()
            if self.cpu.subciclo == 0 or self.cpu.halted:
                break
        self.atualizar_tela()

    def executar_instrucao(self):
        if self.cpu.halted:
            return
        for _ in range(4 * 200):                    # limite de segurança
            self.avancar_subciclo()
            if (self.cpu.subciclo == 0 and self.cpu.mpc == 0) or self.cpu.halted:
                break
        self.atualizar_tela()

    def mudou_velocidade(self, valor):
        self.label_velocidade.configure(text=f"Velocidade: {int(round(valor))}")

    def alternar_execucao(self):
        if self.executando:
            self.pausar()
        elif not self.cpu.halted:
            self.executando = True
            self.btn_executar.configure(text="⏸  Pausar", fg_color="#a87a00", hover_color="#7a5900")
            self.atualizar_botoes()
            self.tick()

    def tick(self):
        if not self.executando:
            return
        intervalo, passos = VELOCIDADES[int(round(self.slider_velocidade.get()))]
        for _ in range(passos):
            if self.cpu.halted:
                break
            self.avancar_subciclo()
        self.atualizar_tela()
        if self.cpu.halted:
            self.pausar()
        else:
            self._after_id = self.after(intervalo, self.tick)

    def pausar(self):
        self.executando = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.btn_executar.configure(text="▶  Executar", fg_color="#2b7a4b", hover_color="#1f5a37")
        self.atualizar_botoes()

    def reiniciar(self):
        self.pausar()
        self.carregar_programa()

if __name__ == "__main__":
    app = Mic1SimulatorApp()
    app.mainloop()