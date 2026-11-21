import pytest

from componentes.controle.memoria_de_controle import MemoriaDeControle
from componentes.controle.mmux import Mmux
from componentes.cpu import decodificar_microinstrucao


@pytest.mark.parametrize("cond, n, z, desvia", [
    (0, True, True, False),      # nunca desvia
    (1, True, False, True),      # se N
    (1, False, True, False),
    (2, False, True, True),      # se Z
    (2, True, False, False),
    (3, False, False, True),     # sempre
])
def test_logica_de_desvio(cond, n, z, desvia):
    proximo = Mmux().calcular_proximo_mpc(mpc_atual=10, cond=cond, addr=50,
                                          flag_n=n, flag_z=z)
    assert proximo == (50 if desvia else 11)


def test_mpc_de_8_bits_da_a_volta():
    assert Mmux().calcular_proximo_mpc(255, 0, 0, False, False) == 0


def test_microprograma_tem_79_microinstrucoes(controle):
    assert all(controle.ler(i) != 0 for i in range(79))
    assert controle.ler(79) == 0                 # a partir daqui está vazio


@pytest.mark.parametrize("endereco, palavra", [
    (0, 0x10C00000),     # mar := pc; rd
    (6, 0x10C03000),     # mar := ir; rd
    (8, 0xF0110000),     # ac := mbr; goto 0
])
def test_microinstrucoes_conhecidas(controle, endereco, palavra):
    assert controle.ler(endereco) == palavra


def test_arquivo_ignora_comentarios_e_linhas_vazias(tmp_path):
    arquivo = tmp_path / "micro.txt"
    arquivo.write_text("# comentário\n\n0x10C00000 # [0]\n1010\n")
    memoria = MemoriaDeControle()
    memoria.carregar_microprograma_arquivo(str(arquivo))
    assert memoria.ler(0) == 0x10C00000
    assert memoria.ler(1) == 0b1010


def test_decodificar_mar_ir_rd():
    campos = decodificar_microinstrucao(0x10C03000)
    assert (campos["ULA"], campos["MAR"], campos["RD"], campos["B"]) == (2, 1, 1, 3)
    assert campos["ENC"] == 0


def test_decodificar_ac_mbr_goto_0():
    campos = decodificar_microinstrucao(0xF0110000)
    assert (campos["AMUX"], campos["COND"], campos["ULA"]) == (1, 3, 2)
    assert (campos["ENC"], campos["C"], campos["ADDR"]) == (1, 1, 0)


def test_decodificar_recusa_palavra_invalida():
    with pytest.raises(ValueError):
        decodificar_microinstrucao(-1)