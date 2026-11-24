from .memoria_principal import MemoriaPrincipal
from .cache import Cache


class ControladorMemoria:
    """Liga o MAR/MBR à memória principal, passando pelas caches."""

    def __init__(self, mar, mbr, tamanho_memoria=4096, linhas_cache=8):
        self.mar = mar
        self.mbr = mbr
        self.memoria = MemoriaPrincipal(tamanho_memoria)
        self.cache_instrucoes = Cache(self.memoria, linhas_cache, "Cache de instruções")
        self.cache_dados = Cache(self.memoria, linhas_cache, "Cache de dados")
        self.ultima_operacao = None     # para a interface mostrar o que aconteceu

    def ler(self, instrucao=False):
        """Sinal rd: memória[MAR] -> MBR."""
        endereco = self.mar.ler()
        cache = self.cache_instrucoes if instrucao else self.cache_dados
        valor = cache.ler(endereco)
        self.mbr.gravar(valor)
        self.ultima_operacao = {"tipo": "leitura", "endereco": endereco,
                                "cache": cache.nome, "resultado": cache.ultimo_acesso}
        return valor

    def escrever(self):
        """Sinal wr: MBR -> memória[MAR]."""
        endereco = self.mar.ler()
        valor = self.mbr.ler()
        # Uma única escrita física; ambas as caches mantêm cópias coerentes.
        self.memoria.escrever(endereco, valor)
        self.cache_dados.atualizar_se_presente(endereco, valor)
        self.cache_instrucoes.atualizar_se_presente(endereco, valor)
        self.ultima_operacao = {"tipo": "escrita", "endereco": endereco, "valor": valor}

    def carregar_programa(self, palavras):
        """Substitui o conteúdo da RAM e invalida as duas caches."""
        palavras = list(palavras)
        if len(palavras) > self.memoria.tamanho:
            raise ValueError("O programa excede a capacidade da memória principal")
        if any(not isinstance(p, int) or not 0 <= p <= 0xFFFF for p in palavras):
            raise ValueError("Cada palavra do programa deve ser um inteiro de 16 bits")
        self.reset()
        self.memoria.carregar_programa(palavras)

    def reset_caches(self):
        """Reinicia as caches, mas mantém todo o conteúdo da RAM."""
        self.cache_instrucoes.reset()
        self.cache_dados.reset()
        self.ultima_operacao = None

    def reset(self):
        self.memoria.reset()
        self.reset_caches()

    def get_state(self):
        return {
            "memoria": list(self.memoria.dados),
            "cache_instrucoes": self.cache_instrucoes.get_state(),
            "cache_dados": self.cache_dados.get_state(),
            "ultima_operacao": dict(self.ultima_operacao) if self.ultima_operacao else None,
        }