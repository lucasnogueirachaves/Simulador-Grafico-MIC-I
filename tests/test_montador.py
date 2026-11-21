import pytest

from montador.checar_erros import ErroDeMontagem
from montador.montador import montar


@pytest.mark.parametrize("fonte, palavra", [
    ("LODD 10", 0x000A), ("STOD 5", 0x1005), ("ADDD 20", 0x2014),
    ("SUBD 3", 0x3003), ("JPOS 4", 0x4004), ("JZER 5", 0x5005),
    ("JUMP 6", 0x6006), ("LOCO 7", 0x7007), ("LODL 1", 0x8001),
    ("STOL 2", 0x9002), ("ADDL 3", 0xA003), ("SUBL 4", 0xB004),
    ("JNEG 7", 0xC007), ("JNZE 8", 0xD008), ("CALL 9", 0xE009),
    ("PSHI", 0xF000), ("POPI", 0xF200), ("PUSH", 0xF400),
    ("POP", 0xF600), ("RETN", 0xF800), ("SWAP", 0xFA00),
    ("INSP 3", 0xFC03), ("DESP 2", 0xFE02),
])
def test_codigo_de_maquina_de_cada_instrucao(fonte, palavra):
    palavras, _, _ = montar(fonte)
    assert palavras == [palavra]


def test_rotulo_vira_endereco():
    palavras, rotulos, _ = montar("inicio: LOCO 1\nJUMP inicio")
    assert palavras == [0x7001, 0x6000]
    assert rotulos == {"INICIO": 0}


def test_rotulo_para_frente():
    palavras, rotulos, _ = montar("JUMP fim\nLOCO 1\nfim: LOCO 2")
    assert palavras[0] == 0x6002
    assert rotulos["FIM"] == 2


def test_variavel_ganha_endereco_depois_do_codigo():
    palavras, _, variaveis = montar("LODD x")
    assert variaveis == {"X": 1}
    assert palavras == [0x0001]


def test_rotulo_inexistente():
    with pytest.raises(ErroDeMontagem) as erro:
        montar("JUMP naoexiste")
    assert erro.value.numero_linha == 1


def test_instrucao_desconhecida():
    with pytest.raises(ErroDeMontagem):
        montar("XPTO 1")


def test_instrucao_sem_operando_obrigatorio():
    with pytest.raises(ErroDeMontagem):
        montar("LOCO")


def test_operando_grande_demais():
    with pytest.raises(ErroDeMontagem):
        montar("LOCO 5000")                    # só cabem 12 bits (até 4095)


def test_erro_informa_a_linha_certa():
    with pytest.raises(ErroDeMontagem) as erro:
        montar("LOCO 1\nLOCO 2\nXPTO 3")
    assert erro.value.numero_linha == 3