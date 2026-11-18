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
        self.cache_dados.escrever(endereco, valor)
        # Se o endereço também estiver na cache de instruções, atualiza a cópia de lá
        self.cache_instrucoes.escrever(endereco, valor)
        self.ultima_operacao = {"tipo": "escrita", "endereco": endereco, "valor": valor}

    def carregar_programa(self, palavras):
        """Recebe a lista de palavras do montador e coloca na memória."""
        self.reset()
        self.memoria.carregar_programa(palavras)

    def reset(self):
        self.memoria.reset()
        self.cache_instrucoes.reset()
        self.cache_dados.reset()
        self.ultima_operacao = None

    def get_state(self):
        return {
            "memoria": self.memoria.dados,
            "cache_instrucoes": self.cache_instrucoes.get_state(),
            "cache_dados": self.cache_dados.get_state(),
            "ultima_operacao": self.ultima_operacao,
        }