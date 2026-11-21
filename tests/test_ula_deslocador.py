import pytest

from componentes.via_de_dados.deslocador import Deslocador
from componentes.via_de_dados.ula import ula


@pytest.mark.parametrize("a, b, op, resultado, n, z", [
    (3, 4, 0, 7, 0, 0),                    # soma
    (0xFFFF, 1, 0, 0, 0, 1),               # estouro: dá a volta e liga Z
    (0x7FFF, 1, 0, 0x8000, 1, 0),          # vira negativo: liga N
    (0x00F0, 0x0FF0, 1, 0x00F0, 0, 0),     # AND
    (5, 9, 2, 5, 0, 0),                    # passa A
    (0, 0, 3, 0xFFFF, 1, 0),               # NOT A
])
def test_operacoes_da_ula(a, b, op, resultado, n, z):
    assert ula(a, b, op) == (resultado, n, z)


def test_operacao_invalida():
    with pytest.raises(ValueError):
        ula(1, 1, 4)


@pytest.mark.parametrize("valor, sh, esperado", [
    (0x0004, 0, 0x0004),    # sem deslocamento
    (0x0004, 1, 0x0002),    # direita
    (0x0004, 2, 0x0008),    # esquerda
    (0x8000, 2, 0x0000),    # esquerda perde o bit mais alto
])
def test_deslocador(valor, sh, esperado):
    d = Deslocador()
    d.execucao(valor, sh)
    assert d.resultado == esperado


def test_deslocador_operacao_invalida():
    with pytest.raises(ValueError):
        Deslocador().execucao(1, 3)