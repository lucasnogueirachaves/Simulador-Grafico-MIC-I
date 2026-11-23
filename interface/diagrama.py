"""Diagrama do datapath do MIC-1, em uma janela à parte (desenhado com Canvas).

Os componentes são desenhados uma única vez; a cada passo a janela só troca os
textos e as cores, destacando o que foi usado no subciclo que acabou de rodar.
"""
import tkinter as tk

import customtkinter as ctk

LARGURA, ALTURA = 1190, 780

COR_FUNDO = "#1a1a1a"
COR_CAIXA = "#262626"
COR_BORDA = "#555555"
COR_TEXTO = "#e6e6e6"
COR_FIO = "#666666"
COR_ATIVO = "#14574a"           # mesmo verde-escuro dos destaques da janela principal
COR_ATIVO_BORDA = "#00ffcc"
COR_A, COR_B, COR_C = "#1f538d", "#a87a00", "#2b7a4b"

FONTE_TITULO = ("Consolas", 9, "bold")
FONTE_VALOR = ("Consolas", 10)

NOMES_REGISTRADORES = ["PC", "AC", "SP", "IR", "TIR", "0", "+1", "-1",
                       "AMASK", "SMASK", "A", "B", "C", "D", "E", "F"]
OPERACOES_ULA = {0: "A + B", 1: "A AND B", 2: "A", 3: "NOT A"}
DESLOCAMENTOS = {0: "sem deslocar", 1: "direita 1 bit", 2: "esquerda 1 bit"}
FASES = ["Busca da microinstrução", "Leitura dos operandos", "ULA e deslocador", "Escrita e próximo MPC"]


def hex16(valor):
    return f"0x{valor:04X}"


class JanelaDiagrama(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Diagrama do datapath - MIC-1")
        self.geometry(f"{LARGURA}x{ALTURA}")
        self.resizable(False, False)
        self.configure(fg_color=COR_FUNDO)

        self.canvas = tk.Canvas(self, width=LARGURA, height=ALTURA, bg=COR_FUNDO, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self._caixas = {}       # nome -> (retângulo, título, valor)
        self._fios = {}         # nome -> linha
        self._linhas_regs = []  # por registrador: (retângulo, nome, valor, marca)
        self._desenhar()
        self.after(200, self.lift)

    # ------------------------------------------------------------------ desenho
    def _caixa(self, nome, x1, y1, x2, y2, titulo, valor=""):
        c = self.canvas
        retangulo = c.create_rectangle(x1, y1, x2, y2, fill=COR_CAIXA, outline=COR_BORDA, width=1)
        t = c.create_text((x1 + x2) / 2, y1 + 11, text=titulo, fill=COR_TEXTO, font=FONTE_TITULO)
        v = c.create_text((x1 + x2) / 2, (y1 + y2) / 2 + 8, text=valor, fill=COR_TEXTO,
                          font=FONTE_VALOR, justify="center")
        self._caixas[nome] = (retangulo, t, v)

    def _fio(self, nome, *pontos, seta=True):
        linha = self.canvas.create_line(*pontos, fill=COR_FIO, width=2,
                                        arrow=tk.LAST if seta else None, arrowshape=(10, 12, 4))
        self._fios[nome] = linha

    def _rotulo(self, x, y, texto):
        self.canvas.create_text(x, y, text=texto, fill="#9a9a9a", font=("Consolas", 8))

    def _desenhar(self):
        c = self.canvas

        # banco de registradores
        self._caixa("banco", 20, 40, 290, 500, "Banco de registradores")
        for i, nome in enumerate(NOMES_REGISTRADORES):
            y = 66 + i * 26
            retangulo = c.create_rectangle(28, y, 282, y + 24, fill=COR_CAIXA, outline=COR_BORDA)
            nome_id = c.create_text(36, y + 12, text=f"{i:>2}  {nome}", anchor="w", fill=COR_TEXTO, font=FONTE_VALOR)
            valor_id = c.create_text(236, y + 12, text="0x0000", anchor="e", fill=COR_TEXTO, font=FONTE_VALOR)
            marca_id = c.create_text(266, y + 12, text="", fill="#ffffff", font=FONTE_TITULO)
            self._linhas_regs.append((retangulo, nome_id, valor_id, marca_id))

        # via de dados
        self._caixa("mbr", 380, 40, 500, 95, "MBR", "0x0000")
        self._caixa("latch_a", 380, 120, 500, 175, "Latch A", "0x0000")
        self._caixa("latch_b", 380, 395, 500, 450, "Latch B", "0x0000")
        self._caixa("mar", 380, 460, 500, 510, "MAR", "0x0000")
        self._caixa("amux", 560, 95, 620, 200, "AMUX", "")
        self._caixa("alu", 700, 130, 830, 290, "ULA", "")
        self._caixa("shifter", 700, 340, 830, 395, "Deslocador", "")
        self._caixa("flags", 880, 175, 980, 225, "Flags", "N: 0  Z: 0")

        # memória e caches
        self._caixa("zona_memoria", 1000, 40, 1170, 520, "Memória e caches")
        self._caixa("cache_i", 1015, 65, 1155, 150, "Cache de instruções", "")
        self._caixa("cache_d", 1015, 160, 1155, 245, "Cache de dados", "")
        self._caixa("memoria", 1015, 255, 1155, 340, "Memória principal", "")
        self._caixa("controlador", 1015, 400, 1155, 500, "Controlador", "---")

        # controle
        self._caixa("mmux", 40, 585, 140, 625, "Mmux", "")
        self._caixa("mpc", 40, 650, 140, 700, "MPC", "0x0")
        self._caixa("memoria_controle", 210, 630, 490, 720, "Memória de controle (256 x 32)", "")
        self._caixa("mir", 560, 610, 1130, 730, "MIR (microinstrução atual)", "")

        # fios da via de dados
        self._fio("bus_a", 290, 147, 380, 147)
        self._fio("bus_b", 290, 422, 380, 422)
        self._fio("latcha_amux", 500, 147, 530, 147, 530, 175, 560, 175)
        self._fio("mbr_amux", 500, 67, 540, 67, 540, 115, 560, 115)
        self._fio("amux_alu", 620, 147, 660, 147, 660, 170, 700, 170)
        self._fio("latchb_alu", 500, 422, 680, 422, 680, 250, 700, 250)
        self._fio("alu_shift", 765, 290, 765, 340)
        self._fio("alu_flags", 830, 200, 880, 200)
        self._fio("shift_c", 765, 395, 765, 540, seta=False)
        self._fio("bus_c", 765, 540, 155, 540, 155, 500)
        self._fio("bus_c_mbr", 345, 540, 345, 67, 380, 67)
        self._fio("latchb_mar", 440, 450, 440, 460)
        self._fio("mar_mem", 500, 485, 1015, 485)
        self._fio("mbr_mem", 440, 40, 440, 22, 1085, 22, 1085, 40)

        # fios do controle
        self._fio("mpc_cs", 140, 675, 210, 675)
        self._fio("cs_mir", 490, 675, 560, 675)
        self._fio("mmux_mpc", 90, 625, 90, 650)
        self._fio("mpc_mmux", 40, 675, 22, 675, 22, 605, 40, 605)
        self._fio("addr_mmux", 700, 610, 700, 600, 140, 600)
        self._fio("flags_mmux", 930, 225, 930, 565, 90, 565, 90, 585)

        for x, y, texto in [(333, 136, "Barr. A"), (333, 411, "Barr. B"), (450, 552, "Barramento C"),
                            (800, 473, "endereço"), (760, 12, "dados (MBR <-> memória)"),
                            (60, 573, "MPC+1"), (420, 593, "ADDR"), (955, 330, "N / Z")]:
            self._rotulo(x, y, texto)

        # legenda e status
        for x, cor, texto in [(20, COR_A, "campo A"), (120, COR_B, "campo B"),
                              (220, COR_C, "campo C"), (320, COR_ATIVO, "ativo")]:
            c.create_rectangle(x, 752, x + 12, 764, fill=cor, outline=COR_BORDA)
            c.create_text(x + 18, 758, text=texto, anchor="w", fill=COR_TEXTO, font=("Consolas", 9))
        self._status = c.create_text(420, 758, text="", anchor="w", fill="#00ffcc", font=FONTE_VALOR)

    # --------------------------------------------------------------- atualização
    def _texto(self, nome, texto):
        self.canvas.itemconfig(self._caixas[nome][2], text=texto)

    def atualizar(self, estado, fase, descricao):
        """Redesenha os valores e destaca o que foi usado na fase que acabou de rodar.

        estado    -- cpu.get_state()
        fase      -- 0 a 3 (subciclo executado) ou None
        descricao -- texto da microinstrução em execução (ex.: "[0] mar := pc; rd;")
        """
        s = estado["sinais"]
        regs = estado["registradores"]
        memoria = estado["memoria"]

        # ---- valores
        for (_, _, valor_id, _), nome in zip(self._linhas_regs, NOMES_REGISTRADORES):
            self.canvas.itemconfig(valor_id, text=hex16(regs[nome]))
        self._texto("latch_a", hex16(estado["barramento_a"]))
        self._texto("latch_b", hex16(estado["barramento_b"]))
        self._texto("mbr", hex16(estado["mbr"]))
        self._texto("mar", f"0x{estado['mar']:03X}")
        self._texto("flags", f"N: {estado['flag_n']}  Z: {estado['flag_z']}")
        self._texto("mpc", f"0x{estado['mpc']:X}")
        self._texto("shifter", hex16(estado["resultado_deslocador"]))

        if s is None:
            self._texto("amux", hex16(estado["entrada_ula_a"]))
            self._texto("alu", hex16(estado["resultado_ula"]))
            self._texto("mir", f"0x{estado['mir']:08X}")
        else:
            origem = "MBR" if s["AMUX"] else "Latch A"
            self._texto("amux", f"{origem}\n{hex16(estado['entrada_ula_a'])}")
            self._texto("alu", f"{OPERACOES_ULA[s['ULA']]}\n{hex16(estado['resultado_ula'])}")
            self._texto("shifter", f"{DESLOCAMENTOS.get(s['DESL'], '?')}\n{hex16(estado['resultado_deslocador'])}")
            self._texto("mir", f"0x{estado['mir']:08X}\n"
                               f"AMUX={s['AMUX']} COND={s['COND']} ULA={s['ULA']} DESL={s['DESL']} "
                               f"MBR={s['MBR']} MAR={s['MAR']}\n"
                               f"RD={s['RD']} WR={s['WR']} ENC={s['ENC']} "
                               f"C={s['C']} B={s['B']} A={s['A']} ADDR={s['ADDR']}")
        self._texto("memoria_controle", descricao.replace("] ", "]\n", 1) if descricao != "---" else "---")

        for nome, chave in (("cache_i", "cache_instrucoes"), ("cache_d", "cache_dados")):
            cache = memoria[chave]
            self._texto(nome, f"hits: {cache['hits']}  misses: {cache['misses']}\n"
                              f"último: {cache['ultimo_acesso'] or '---'}")
        operacao = memoria["ultima_operacao"]
        if isinstance(operacao, dict):
            ultima = f"{operacao.get('tipo', '?')} end. {operacao.get('endereco', '?')}"
        else:
            ultima = str(operacao) if operacao else "---"
        self._texto("memoria", f"{len(memoria['memoria'])} palavras\núltima op.:\n{ultima}")
        if s is not None and fase == 3 and (s["RD"] or s["WR"]):
            self._texto("controlador", "leitura (RD)" if s["RD"] else "escrita (WR)")
        else:
            self._texto("controlador", "---")

        # ---- o que está ativo nesta fase
        caixas, fios = set(), set()
        linhas_regs = {}                      # índice do registrador -> (cor, marca)
        if s is not None and fase is not None:
            if fase == 0:
                caixas |= {"mpc", "memoria_controle", "mir"}
                fios |= {"mpc_cs", "cs_mir"}
            elif fase == 1:
                caixas |= {"banco", "latch_a", "latch_b"}
                fios |= {"bus_a", "bus_b"}
                linhas_regs[s["A"]] = (COR_A, "A")
                if s["B"] == s["A"]:
                    linhas_regs[s["A"]] = (COR_A, "A B")
                else:
                    linhas_regs[s["B"]] = (COR_B, "B")
            elif fase == 2:
                caixas |= {"amux", "alu", "shifter", "flags", "latch_b"}
                fios |= {"amux_alu", "latchb_alu", "alu_shift", "alu_flags"}
                if s["AMUX"]:
                    caixas.add("mbr")
                    fios.add("mbr_amux")
                else:
                    caixas.add("latch_a")
                    fios.add("latcha_amux")
            else:
                caixas |= {"shifter", "mmux", "mpc"}
                fios.add("mmux_mpc")
                cond = s["COND"]
                desvia = (cond == 3 or (cond == 1 and estado["flag_n"] == 1)
                          or (cond == 2 and estado["flag_z"] == 1))
                fios.add("addr_mmux" if desvia else "mpc_mmux")
                if cond in (1, 2):
                    fios.add("flags_mmux")
                    caixas.add("flags")
                if s["ENC"]:
                    caixas.add("banco")
                    fios |= {"shift_c", "bus_c"}
                    linhas_regs[s["C"]] = (COR_C, "C")
                if s["MBR"]:
                    caixas.add("mbr")
                    fios |= {"shift_c", "bus_c_mbr"}
                if s["MAR"]:
                    caixas |= {"mar", "latch_b"}
                    fios.add("latchb_mar")
                if s["RD"] or s["WR"]:
                    caixas |= {"controlador", "cache_d", "memoria"}
                    fios |= {"mar_mem", "mbr_mem"}

        c = self.canvas
        for nome, (retangulo, _, _) in self._caixas.items():
            ativo = nome in caixas
            c.itemconfig(retangulo, fill=COR_ATIVO if ativo else COR_CAIXA,
                         outline=COR_ATIVO_BORDA if ativo else COR_BORDA, width=2 if ativo else 1)
        for nome, linha in self._fios.items():
            ativo = nome in fios
            c.itemconfig(linha, fill=COR_ATIVO_BORDA if ativo else COR_FIO, width=3 if ativo else 2)
        for i, (retangulo, _, _, marca) in enumerate(self._linhas_regs):
            cor, texto = linhas_regs.get(i, (COR_CAIXA, ""))
            c.itemconfig(retangulo, fill=cor)
            c.itemconfig(marca, text=texto)

        if fase is None:
            c.itemconfig(self._status, text="Aguardando o primeiro passo")
        else:
            c.itemconfig(self._status, text=f"Fase {fase + 1}/4: {FASES[fase]}   |   {descricao}")