"""Testes de integração: montador + microprograma + via de dados + memória."""
import pytest


def test_cpu_comeca_no_inicio_do_microprograma(cpu):
    assert cpu.mpc == 0


def test_lodd_leva_9_microinstrucoes(cpu, rodar):
    # busca (3) + decodificação (3) + execução (3) = 9 ciclos de microinstrução
    resultado = rodar("LODD x", 1, dados={"x": 42})
    assert resultado.ac == 42
    assert resultado.pc == 1


def test_aritmetica_basica(rodar):
    r = rodar("LODD a\nADDD b\nSTOD c\nSUBD a\nSTOD d", 5, dados={"a": 10, "b": 3})
    assert r.var("c") == 13
    assert r.var("d") == 3
    assert r.ac == 3


def test_loco_stod_addd(rodar):
    r = rodar("LOCO 7\nSTOD x\nADDD x", 3)
    assert r.ac == 14
    assert r.var("x") == 7
    assert r.pc == 3


def test_laco_de_contagem_com_jzer_e_jump(rodar):
    fonte = "LODD n\nloop: JZER fim\nSUBD um\nSTOD n\nJUMP loop\nfim: LODD n"
    # 1 + 3 voltas de 4 instruções + JZER que sai + LODD final = 15 instruções
    r = rodar(fonte, 15, dados={"n": 3, "um": 1})
    assert r.ac == 0
    assert r.var("n") == 0
    assert r.pc == r.rotulos["FIM"] + 1


def test_push_e_pop(rodar):
    r = rodar("LOCO 5\nPUSH\nLOCO 9\nPOP\nSTOD x", 5)
    assert r.ac == 5
    assert r.sp == 100
    assert r.var("x") == 5


def test_call_e_retn(rodar):
    fonte = "CALL sub\nSTOD r\nJUMP fim\nsub: LOCO 7\nRETN\nfim: LOCO 1"
    r = rodar(fonte, 4)                         # CALL, LOCO, RETN, STOD
    assert r.ac == 7
    assert r.var("r") == 7
    assert r.sp == 100                          # a pilha voltou ao lugar
    assert r.pc == 2                            # parou no JUMP, logo após o STOD


def test_enderecamento_relativo_ao_sp(rodar):
    r = rodar("LODL 4\nADDL 4\nSTOL 3\nSUBL 4", 4, memoria={104: 11})
    assert r.ac == 11
    assert r.mem[103] == 22


def test_desp_diminui_o_sp(rodar):
    assert rodar("DESP 2", 1).sp == 98


def test_insp_desfaz_o_desp(rodar):
    assert rodar("DESP 2\nINSP 2", 2).sp == 100


def test_swap(rodar):
    r = rodar("LOCO 50\nSWAP", 2)
    assert (r.ac, r.sp) == (100, 50)


def test_pshi_e_popi(rodar):
    r = rodar("LOCO 200\nPSHI\nLOCO 201\nPOPI", 4, memoria={200: 77})
    assert r.mem[201] == 77
    assert r.sp == 100


def test_jpos_jneg_jnze_com_ac_positivo(rodar):
    fonte = ("LOCO 5\nJPOS pula\nLOCO 99\npula: JNEG fora\nJNZE fim\n"
             "LOCO 98\nfim: LOCO 3\nfora: LOCO 97")
    r = rodar(fonte, 4)                         # LOCO, JPOS (salta), JNEG (não), JNZE (salta)
    assert r.ac == 5
    assert r.pc == r.rotulos["FIM"]


def test_jneg_com_ac_negativo(rodar):
    fonte = "LODD z\nSUBD u\nJNEG alvo\nLOCO 99\nalvo: LOCO 4"
    r = rodar(fonte, 3, dados={"z": 0, "u": 1})
    assert r.ac == 0xFFFF                       # -1 em 16 bits
    assert r.pc == r.rotulos["ALVO"]


def test_busca_de_instrucao_usa_a_cache_de_instrucoes(rodar):
    r = rodar("LOCO 1\nLOCO 2\nLOCO 3", 3)
    cache = r.cpu.memoria.cache_instrucoes
    assert cache.hits + cache.misses > 0