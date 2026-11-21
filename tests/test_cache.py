from componentes.memoria.cache import Cache


class MemoriaFalsa:
    """Memória mínima para testar a cache sem a memória de verdade."""

    def __init__(self):
        self.dados = {}

    def ler(self, endereco):
        return self.dados.get(endereco, 0)

    def escrever(self, endereco, valor):
        self.dados[endereco] = valor


def nova_cache(linhas=4):
    memoria = MemoriaFalsa()
    return Cache(memoria, num_linhas=linhas), memoria


def test_primeiro_acesso_e_miss_e_o_segundo_e_hit():
    cache, memoria = nova_cache()
    memoria.dados[7] = 42
    assert cache.ler(7) == 42
    assert cache.ultimo_acesso == "miss"
    assert cache.ler(7) == 42
    assert cache.ultimo_acesso == "hit"
    assert (cache.hits, cache.misses) == (1, 1)


def test_conflito_enderecos_na_mesma_linha_se_expulsam():
    cache, _ = nova_cache(linhas=4)             # 0 e 4 caem na mesma linha
    for endereco in (0, 4, 0):
        cache.ler(endereco)
    assert (cache.hits, cache.misses) == (0, 3)


def test_segunda_passada_so_tem_hits_se_cabe_tudo():
    cache, _ = nova_cache(linhas=4)
    for _ in range(2):
        for endereco in range(4):
            cache.ler(endereco)
    assert (cache.hits, cache.misses) == (4, 4)


def test_escrita_vai_direto_para_a_memoria():
    cache, memoria = nova_cache()
    cache.escrever(5, 99)
    assert memoria.dados[5] == 99               # write-through


def test_escrita_atualiza_a_linha_quando_ha_hit():
    cache, memoria = nova_cache()
    cache.ler(5)                                # traz o endereço 5 para a cache
    cache.escrever(5, 7)
    assert cache.ler(5) == 7
    assert cache.ultimo_acesso == "hit"
    assert memoria.dados[5] == 7


def test_escrita_sem_hit_nao_aloca_linha():
    cache, _ = nova_cache()
    cache.escrever(5, 99)
    cache.ler(5)
    assert cache.ultimo_acesso == "miss"


def test_reset_zera_contadores_e_linhas():
    cache, _ = nova_cache()
    cache.ler(1)
    cache.reset()
    assert (cache.hits, cache.misses) == (0, 0)
    assert not any(cache.valido)


def test_get_state_tem_o_que_a_interface_precisa():
    cache, _ = nova_cache(linhas=4)
    cache.ler(1)
    estado = cache.get_state()
    assert estado["misses"] == 1
    assert len(estado["linhas"]) == 4
    assert estado["linhas"][1]["valido"] is True