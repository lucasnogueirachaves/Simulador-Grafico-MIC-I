"""Preparação compartilhada pelos testes (fixtures do pytest)."""
from pathlib import Path

import pytest

from componentes.controle.memoria_de_controle import MemoriaDeControle
from componentes.cpu import CPU
from montador.montador import montar

RAIZ = Path(__file__).resolve().parent.parent
MICROPROGRAMA = RAIZ / "assets" / "microprograma.txt"


class Resultado:
    """O que sobra depois de rodar um programa."""

    def __init__(self, cpu, rotulos, variaveis):
        self.cpu = cpu
        self.rotulos = rotulos
        self.variaveis = variaveis
        regs = cpu.registradores.registradores
        self.pc = regs[0].valor
        self.ac = regs[1].valor
        self.sp = regs[2].valor
        self.mem = cpu.memoria.memoria.dados

    def var(self, nome):
        """Valor atual de uma variável do programa."""
        return self.mem[self.variaveis[nome.upper()]]


@pytest.fixture
def controle():
    """Memória de controle com o microprograma carregado."""
    memoria_de_controle = MemoriaDeControle()
    memoria_de_controle.carregar_microprograma_arquivo(str(MICROPROGRAMA))
    return memoria_de_controle


@pytest.fixture
def cpu(controle):
    """CPU nova, ligada ao microprograma."""
    return CPU(controle)


@pytest.fixture
def rodar(cpu):
    """Monta um programa, executa N instruções e devolve um Resultado.

    fonte      -- texto assembly
    instrucoes -- quantas instruções do assembly executar
    dados      -- {variavel: valor inicial}
    memoria    -- {endereco: valor inicial}
    sp         -- valor inicial do SP

    Chame uma vez por teste: ela reaproveita a mesma CPU (fixture cpu).
    """
    def _rodar(fonte, instrucoes, dados=None, memoria=None, sp=100):
        palavras, rotulos, variaveis = montar(fonte)
        for endereco, palavra in enumerate(palavras):
            cpu.memoria.memoria.escrever(endereco, palavra)
        for nome, valor in (dados or {}).items():
            cpu.memoria.memoria.escrever(variaveis[nome.upper()], valor)
        for endereco, valor in (memoria or {}).items():
            cpu.memoria.memoria.escrever(endereco, valor)
        cpu.registradores.registradores[2].gravar(sp)

        concluidas = 0
        for _ in range(instrucoes * 100):          # limite de segurança
            cpu.executar_ciclo()
            if cpu.mpc == 0 and cpu.subciclo == 0:   # voltou ao início da busca
                concluidas += 1
                if concluidas == instrucoes:
                    return Resultado(cpu, rotulos, variaveis)
        raise AssertionError(f"o programa não terminou {instrucoes} instrução(ões)")

    return _rodar