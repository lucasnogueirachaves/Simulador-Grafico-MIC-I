import pytest

from componentes.via_de_dados.registradores.banco_registradores import BancoRegistradores
from componentes.via_de_dados.registradores.registrador import Registrador
from componentes.via_de_dados.registradores.registrador_constante import RegistradorConstante


def test_gravar_e_ler():
    r = Registrador("AC")
    r.gravar(1234)
    assert r.ler() == 1234


def test_estouro_de_16_bits_da_a_volta():
    r = Registrador("AC")
    r.gravar(65536)
    assert r.ler() == 0


def test_negativo_fica_em_complemento_de_dois():
    r = Registrador("AC")
    r.gravar(-1)
    assert r.ler() == 0xFFFF


def test_largura_de_12_bits_como_o_mar():
    r = Registrador("MAR", largura=12)
    r.gravar(0xFFFF)
    assert r.ler() == 0x0FFF


def test_indicador_ativo_para_o_diagrama():
    r = Registrador("PC")
    assert r.ativo is False
    r.ler()
    assert r.ativo is True
    r.resetar()
    assert r.ativo is False and r.valor == 0


def test_constante_ignora_escrita():
    r = RegistradorConstante("+1", 1)
    r.gravar(99)
    assert r.ler() == 1


def test_constante_menos_um_vale_ffff():
    assert RegistradorConstante("-1", -1).ler() == 0xFFFF


def test_banco_tem_16_registradores_na_ordem_do_livro():
    nomes = [r.identificador for r in BancoRegistradores().registradores]
    assert nomes == ["PC", "AC", "SP", "IR", "TIR", "0", "+1", "-1",
                     "AMASK", "SMASK", "A", "B", "C", "D", "E", "F"]


@pytest.mark.parametrize("endereco, valor", [(8, 0x0FFF), (9, 0x00FF), (5, 0), (6, 1)])
def test_banco_constantes(endereco, valor):
    assert BancoRegistradores().ler(endereco) == valor


def test_banco_gravar_por_endereco():
    banco = BancoRegistradores()
    banco.gravar(2, 100)                       # SP
    assert banco.ler(2) == 100