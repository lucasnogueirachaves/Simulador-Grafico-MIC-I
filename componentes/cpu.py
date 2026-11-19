from .via_de_dados.ULA import ula
from .via_de_dados.Deslocador import Deslocador
from .via_de_dados.mar import Mar
from .via_de_dados.mbr import Mbr
from .via_de_dados.registradores.banco_registradores import BancoRegistradores
from .memoria.controlador_memoria import ControladorMemoria

"""correções relacionadas a conexão com outros arquivos do projeto ainda precisam ser feitas,
   mas a lógica da cpu está estruturada com exceção de algumas funções :)"""

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
        self.reset()

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
        self.mpc = 0
        self.mir = 0
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
        self.microinstrucoes_executadas = 0
        self.deslocador.entrada = 0
        self.deslocador.resultado = 0
        self.deslocador.sh = 0

    def buscar_microinstrucao(self):
        # Subciclo 0: acesso à memória de controle e carregamento do MIR.
        self.mir = self._ler_memoria_controle(self.mpc)
        self.sinais = decodificar_microinstrucao(self.mir)
        self.componentes_ativos = ["MPC", "MIR", "MEMORIA_CONTROLE"]

    def ler_operandos(self):
        # Subciclo 1: latches de entrada da ULA.
        s = self.sinais
        if s is None:
            raise RuntimeError("Nenhuma microinstrução foi carregada.")
        self.barramento_a = self.registradores.ler(s["A"])
        self.barramento_b = self.registradores.ler(s["B"])
        self.entrada_ula_a = self.mbr.ler() if s["AMUX"] else self.barramento_a
        self.componentes_ativos = ["BARRAMENTO_A", "BARRAMENTO_B", "AMUX"]

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

    def escrever_resultado(self):
        # Subciclo 3: todos os destinos veem os valores do MESMO ciclo.
        s = self.sinais
        if s is None:
            raise RuntimeError("Nenhuma microinstrução foi carregada.")
        saida = self.resultado_deslocador
        self.componentes_ativos = []

        # MAR é alimentado pelo barramento B, não pela saída da ULA.
        if s["MAR"]:
            self.mar.gravar(self.barramento_b)
            self.componentes_ativos.append("MAR")
        if s["MBR"]:
            self.mbr.gravar(saida)
            self.componentes_ativos.append("MBR")
        if s["ENC"]:
            self.registradores.gravar(s["C"], saida)
            self.componentes_ativos.append("BARRAMENTO_C")

        # Modelo funcional: a memória responde imediatamente aos comandos.
        # A distinção de latência/cache poderá ser acrescentada posteriormente.
        if s["RD"]:
            self.memoria.ler()
            self.componentes_ativos.append("RD")
        if s["WR"]:
            self.memoria.escrever()
            self.componentes_ativos.append("WR")

        # COND: 0 sequencial, 1 N, 2 Z, 3 incondicional.
        cond = s["COND"]
        desviar = (cond == 3 or (cond == 1 and self.flag_n == 1)
                   or (cond == 2 and self.flag_z == 1))
        self.mpc = s["ADDR"] if desviar else (self.mpc + 1) & 0xFF
        self.microinstrucoes_executadas += 1
        self.componentes_ativos.append("MPC")

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
        etapas[self.subciclo]()
        self.subciclo = (self.subciclo + 1) % 4

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
            "memoria": self.memoria.get_state(),
        }
