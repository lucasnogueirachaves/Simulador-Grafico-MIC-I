"""Regressões da integração CPU, caches e estado disponibilizado à interface."""
from componentes.controle.memoria_de_controle import MemoriaDeControle
from componentes.cpu import CPU
from componentes.memoria.controlador_memoria import ControladorMemoria
from componentes.via_de_dados.mar import Mar
from componentes.via_de_dados.mbr import Mbr


def novo_controlador():
    return ControladorMemoria(Mar(), Mbr())


def test_escrita_memoria_uma_vez_e_caches_coerentes(monkeypatch):
    memoria = novo_controlador()
    memoria.memoria.escrever(12, 3)
    assert memoria.cache_instrucoes.ler(12) == 3
    assert memoria.cache_dados.ler(12) == 3
    real_escrever = memoria.memoria.escrever
    escritas = []

    def monitorar(endereco, valor):
        escritas.append((endereco, valor))
        real_escrever(endereco, valor)

    monkeypatch.setattr(memoria.memoria, "escrever", monitorar)
    memoria.mar.gravar(12)
    memoria.mbr.gravar(99)
    memoria.escrever()
    assert escritas == [(12, 99)]
    assert memoria.cache_instrucoes.ler(12) == 99
    assert memoria.cache_dados.ler(12) == 99


def test_carregamento_invalida_cache_e_remove_conteudo_antigo():
    cpu = CPU()
    cpu.carregar_programa([5, 17])
    assert cpu.memoria.cache_instrucoes.ler(0) == 5
    assert cpu.memoria.cache_dados.ler(0) == 5
    cpu.carregar_programa([123])
    assert cpu.memoria.cache_instrucoes.misses == 0
    assert cpu.memoria.cache_dados.misses == 0
    assert cpu.memoria.cache_instrucoes.ler(0) == 123
    assert cpu.memoria.cache_dados.ler(0) == 123
    assert cpu.memoria.memoria.ler(1) == 0
    assert cpu.mpc == 0
    assert cpu.fim_do_programa == 1


def test_busca_macroinstrucao_usa_cache_instrucoes(rodar):
    r = rodar("LOCO 1\nLOCO 2\nLOCO 3", 3)
    assert r.cpu.memoria.cache_instrucoes.misses >= 1
    assert r.cpu.memoria.cache_instrucoes.hits >= 1
    assert r.cpu.memoria.cache_dados.hits + r.cpu.memoria.cache_dados.misses == 0


def test_lodd_consulta_ambas_caches(rodar):
    r = rodar("LODD x", 1, dados={"x": 42})
    assert r.ac == 42
    assert r.cpu.memoria.cache_instrucoes.misses >= 1
    assert r.cpu.memoria.cache_dados.misses >= 1


def test_reset_sem_limpeza_preserva_ram_e_invalida_cache():
    cpu = CPU()
    cpu.carregar_programa([0x7005])
    cpu.memoria.cache_instrucoes.ler(0)
    cpu.reset(limpar_memoria=False)
    assert cpu.memoria.memoria.ler(0) == 0x7005
    assert cpu.memoria.cache_instrucoes.misses == 0
    assert not any(cpu.memoria.cache_instrucoes.valido)
    assert cpu.fim_do_programa == 1


def test_get_state_isolado_da_memoria_real():
    cpu = CPU()
    cpu.carregar_programa([0x7005])
    cpu.memoria.mar.gravar(0)
    cpu.memoria.ler(instrucao=True)
    estado = cpu.get_state()
    estado["memoria"]["memoria"][0] = 0xFFFF
    estado["memoria"]["cache_instrucoes"]["linhas"][0]["dado"] = 0xFFFF
    estado["memoria"]["ultima_operacao"]["endereco"] = 999
    assert cpu.memoria.memoria.ler(0) == 0x7005
    assert cpu.memoria.cache_instrucoes.ler(0) == 0x7005
    assert cpu.memoria.ultima_operacao["endereco"] == 0


def test_sinais_de_visualizacao_nao_modificam_cpu(controle):
    cpu = CPU(controle)
    cpu.carregar_programa([0x7005])
    cpu.executar_subciclo()
    estado = cpu.get_state()
    assert estado["ultima_etapa_executada"] == 0
    assert estado["componentes_ativos"] == ["MPC", "MIR", "MEMORIA_CONTROLE"]
    assert estado["transferencias"]
    estado["transferencias"].append("invalido")
    assert "invalido" not in cpu.transferencias


def test_programa_invalido_nao_destroi_programa_anterior():
    cpu = CPU()
    cpu.carregar_programa([0x7005])
    try:
        cpu.carregar_programa([0x10000])
        assert False, "valor fora de 16 bits deve falhar"
    except ValueError:
        pass
    assert cpu.memoria.memoria.ler(0) == 0x7005
