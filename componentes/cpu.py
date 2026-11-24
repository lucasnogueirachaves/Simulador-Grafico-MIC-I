from .via_de_dados.ula import ula
from .via_de_dados.deslocador import Deslocador
from .via_de_dados.mar import Mar
from .via_de_dados.mbr import Mbr
from .via_de_dados.registradores.banco_registradores import BancoRegistradores
from .memoria.controlador_memoria import ControladorMemoria
from .controle.mir import Mir
from .controle.mpc import Mpc
from .controle.mmux import Mmux
from .via_de_dados.amux import Amux
from .via_de_dados.latches import Latchs

"""Coordenação dos quatro subciclos da CPU MIC-1."""

def decodificar_microinstrucao(palavra):
    """Extrai os campos, na ordem MSB->LSB da imagem do projeto."""
    if not isinstance(palavra, int) or not 0 <= palavra <= 0xFFFFFFFF:
        raise ValueError("A microinstrução deve ser um inteiro de 32 bits")

    campos = (
        ("ADDR", 8), ("A", 4), ("B", 4), ("C", 4),
        ("ENC", 1), ("WR", 1), ("RD", 1), ("MAR", 1),
        ("MBR", 1), ("DESL", 2), ("ULA", 2),
        ("COND", 2), ("AMUX", 1),
    )
    resultado = {}
    for nome, largura in campos:
        resultado[nome] = palavra & ((1 << largura) - 1)
        palavra >>= largura
    return resultado


class CPU:
    """Executa um subciclo por chamada, expondo o estado para a GUI."""

    def __init__(self, controle=None):
        # O módulo de controle é responsável por disponibilizar o microprograma.
        self.controle = controle
        self.registradores = BancoRegistradores()
        self.mar = Mar()
        self.mbr = Mbr()
        self.deslocador = Deslocador()
        self.memoria = ControladorMemoria(self.mar, self.mbr)
        # Componentes do controle e da via de dados que antes eram feitos "na mão"
        self._mpc = Mpc()
        self._mir = Mir()
        self.mmux = Mmux()
        self.amux = Amux()
        self.latch_a = Latchs()
        self.latch_b = Latchs()
        self.reset()

    @property
    def mpc(self):
        """Valor do MPC (inteiro), como antes."""
        return self._mpc.valor

    @property
    def mir(self):
        """Valor do MIR (inteiro de 32 bits), como antes."""
        return self._mir.valor

    def conectar_controle(self, controle):
        """Conecta a futura memória de controle sem recriar a CPU."""
        if not callable(getattr(controle, "ler", None)):
            raise TypeError("O controle precisa oferecer ler(endereco) -> int")
        self.controle = controle

    def _ler_memoria_controle(self, endereco):
        """PONTO DE INTEGRAÇÃO: leitura da microinstrução no controle.

        A equipe pode substituir a implementação ou conectar um objeto com
        ler(endereco). Não devolve zeros fictícios quando falta o controle.
        """
        if self.controle is None:
            raise NotImplementedError(
                "Memória de controle não conectada. "
                "Use cpu.conectar_controle(controle)."
            )
        return self.controle.ler(endereco)

    def reset(self, limpar_memoria=True):
        """Volta ao início do microprograma; opcionalmente limpa a RAM."""
        for registrador in self.registradores.registradores:
            registrador.resetar()
        self.mar.resetar()
        self.mbr.resetar()
        if limpar_memoria:
            self.memoria.reset()
            self.fim_do_programa = None  # Não há programa após limpar a RAM.
        else:
            self.memoria.reset_caches()  # Preserva RAM, zera estatísticas de cache.
        self._mpc.resetar()
        self._mir.resetar()
        self.latch_a.carregar(0)
        self.latch_b.carregar(0)
        self.sinais = None
        self.subciclo = 0
        self.halted = False
        self.barramento_a = 0
        self.barramento_b = 0
        self.entrada_ula_a = 0
        self.resultado_ula = 0
        self.resultado_deslocador = 0
        self.flag_n = 0
        self.flag_z = 0
        self.componentes_ativos = []
        self.transferencias = []
        self.ultima_etapa_executada = None
        self.microinstrucoes_executadas = 0
        self.deslocador.entrada = 0
        self.deslocador.resultado = 0
        self.deslocador.sh = 0

    def carregar_programa(self, palavras):
        """Escreve o programa a partir do endereço 0 e marca onde ele termina.

        Quando o PC passar da última instrução, a CPU para (halted = True).
        Um programa vazio já começa parado.
        """
        palavras = list(palavras)
        # O controlador valida todo o programa e invalida caches antigas.
        self.memoria.carregar_programa(palavras)
        self.reset(limpar_memoria=False)
        self.fim_do_programa = len(palavras)
        self.halted = not palavras

    def _verificar_fim_do_programa(self):
        """Para a CPU ao terminar uma instrução cujo PC já passou do programa."""
        terminou_instrucao = self.subciclo == 0 and self.mpc == 0
        if (terminou_instrucao and self.fim_do_programa is not None
                and self.registradores.registradores[0].valor >= self.fim_do_programa):
            self.halted = True

    def buscar_microinstrucao(self):
        # Subciclo 0: acesso à memória de controle e carregamento do MIR.
        self._mir.gravar(self._ler_memoria_controle(self.mpc))
        self.sinais = decodificar_microinstrucao(self.mir)
        self.componentes_ativos = ["MPC", "MIR", "MEMORIA_CONTROLE"]
        self.transferencias = [f"Controle[{self.mpc:02X}] → MIR"]

    def ler_operandos(self):
        # Subciclo 1: latches de entrada da ULA.
        s = self.sinais
        if s is None:
            raise RuntimeError("Nenhuma microinstrução foi carregada.")
        self.latch_a.carregar(self.registradores.ler(s["A"]))
        self.latch_b.carregar(self.registradores.ler(s["B"]))
        self.barramento_a = self.latch_a.ler()
        self.barramento_b = self.latch_b.ler()
        self.entrada_ula_a = self.amux.selecionar(s["AMUX"], self.latch_a.ler(), self.mbr.valor)
        self.componentes_ativos = ["BARRAMENTO_A", "BARRAMENTO_B", "AMUX", "LATCH_A", "LATCH_B"]
        self.transferencias = [
            f"R{s['A']} → A ({self.barramento_a:04X})",
            f"R{s['B']} → B ({self.barramento_b:04X})",
            "MBR → ULA A" if s["AMUX"] else "Latch A → ULA A",
        ]

    def executar_ula(self):
        # Subciclo 2: a ULA calcula flags ANTES do deslocador.
        s = self.sinais
        if s is None:
            raise RuntimeError("Nenhuma microinstrução foi carregada.")
        self.resultado_ula, self.flag_n, self.flag_z = ula(
            self.entrada_ula_a, self.barramento_b, s["ULA"]
        )
        self.resultado_deslocador = self.deslocador.execucao(
            self.resultado_ula, s["DESL"]
        )
        self.componentes_ativos = ["ULA", "DESLOCADOR", "N", "Z"]
        self.transferencias = [
            f"ULA: {self.entrada_ula_a:04X}, {self.barramento_b:04X} → {self.resultado_ula:04X}",
            f"Deslocador → {self.resultado_deslocador:04X}",
        ]

    def escrever_resultado(self):
        # Subciclo 3: todos os destinos veem os valores do MESMO ciclo.
        s = self.sinais
        if s is None:
            raise RuntimeError("Nenhuma microinstrução foi carregada.")
        saida = self.resultado_deslocador
        self.componentes_ativos = []
        self.transferencias = []

        # MAR é alimentado pelo barramento B, não pela saída da ULA.
        if s["MAR"]:
            self.mar.gravar(self.barramento_b)
            self.componentes_ativos.append("MAR")
            self.transferencias.append(f"B → MAR ({self.mar.valor:03X})")
        if s["MBR"]:
            self.mbr.gravar(saida)
            self.componentes_ativos.append("MBR")
            self.transferencias.append(f"Deslocador → MBR ({self.mbr.valor:04X})")
        if s["ENC"]:
            self.registradores.gravar(s["C"], saida)
            self.componentes_ativos.append("BARRAMENTO_C")
            self.transferencias.append(f"C → R{s['C']} ({saida:04X})")

        # Modelo funcional: a memória responde imediatamente aos comandos.
        # A distinção de latência/cache poderá ser acrescentada posteriormente.
        if s["RD"]:
            # No microprograma distribuído, os endereços 0 e 1 buscam
            # macroinstruções. Os demais RD acessam dados.
            busca_instrucao = self.mpc in (0, 1)
            valor = self.memoria.ler(instrucao=busca_instrucao)
            self.componentes_ativos.extend(("RD", "CACHE_INSTRUCOES" if busca_instrucao else "CACHE_DADOS"))
            self.transferencias.append(f"Memória[{self.mar.valor:03X}] → MBR ({valor:04X})")
        if s["WR"]:
            self.memoria.escrever()
            self.componentes_ativos.extend(("WR", "CACHE_DADOS", "CACHE_INSTRUCOES"))
            self.transferencias.append(f"MBR → Memória[{self.mar.valor:03X}]")

        # Próximo MPC: o Mmux decide entre MPC + 1 e o campo ADDR (COND, N e Z)
        self._mpc.gravar(self.mmux.calcular_proximo_mpc(
            self.mpc, s["COND"], s["ADDR"], self.flag_n == 1, self.flag_z == 1))
        self.microinstrucoes_executadas += 1
        self.componentes_ativos.append("MPC")
        self.transferencias.append(f"Próximo MPC = {self.mpc:02X}")

    def executar_subciclo(self):
        """Avança uma etapa (0=busca, 1=leitura, 2=ULA, 3=escrita)."""
        if self.halted:
            return
        etapas = (
            self.buscar_microinstrucao,
            self.ler_operandos,
            self.executar_ula,
            self.escrever_resultado,
        )
        etapa_executada = self.subciclo
        etapas[etapa_executada]()
        self.ultima_etapa_executada = etapa_executada
        self.subciclo = (etapa_executada + 1) % 4
        self._verificar_fim_do_programa()

    def executar_ciclo(self):
        """Conclui a microinstrução atual (não necessariamente 4 passos)."""
        if self.halted:
            return
        quantidade = 4 - self.subciclo
        for _ in range(quantidade):
            self.executar_subciclo()

    def get_state(self):
        """Retorna um retrato dos sinais e dos componentes para a interface."""
        return {
            "subciclo": self.subciclo,
            "ultima_etapa_executada": self.ultima_etapa_executada,
            "mpc": self.mpc,
            "mir": self.mir,
            "sinais": dict(self.sinais) if self.sinais is not None else None,
            "halted": self.halted,
            "controle_conectado": self.controle is not None,
            "microinstrucoes_executadas": self.microinstrucoes_executadas,
            "barramento_a": self.barramento_a,
            "barramento_b": self.barramento_b,
            "entrada_ula_a": self.entrada_ula_a,
            "resultado_ula": self.resultado_ula,
            "resultado_deslocador": self.resultado_deslocador,
            "flag_n": self.flag_n,
            "flag_z": self.flag_z,
            "mar": self.mar.valor,
            "mbr": self.mbr.valor,
            "registradores": {
                r.identificador: r.valor for r in self.registradores.registradores
            },
            "componentes_ativos": list(self.componentes_ativos),
            "transferencias": list(self.transferencias),
            "memoria": self.memoria.get_state(),
        }