class Cache:
    """Cache de mapeamento direto com política write-through."""

    def __init__(self, memoria, num_linhas=8, nome="Cache"):
        self.memoria = memoria         
        self.num_linhas = num_linhas
        self.nome = nome
        self.reset()

    def reset(self):
        self.valido = [False] * self.num_linhas
        self.tag = [0] * self.num_linhas
        self.dado = [0] * self.num_linhas
        self.hits = 0
        self.misses = 0
        self.ultimo_acesso = None       

    def _linha_e_tag(self, endereco):
        return endereco % self.num_linhas, endereco // self.num_linhas

    def _esta_na_cache(self, linha, tag):
        return self.valido[linha] and self.tag[linha] == tag

    def ler(self, endereco):
        linha, tag = self._linha_e_tag(endereco)
        if self._esta_na_cache(linha, tag):
            self.hits += 1
            self.ultimo_acesso = "hit"
        else:
            self.misses += 1
            self.ultimo_acesso = "miss"
            self.valido[linha] = True
            self.tag[linha] = tag
            self.dado[linha] = self.memoria.ler(endereco)
        return self.dado[linha]

    def atualizar_se_presente(self, endereco, valor):
        """Mantém uma cópia já carregada coerente, sem escrever na RAM.

        Write-no-allocate: se o endereço não estiver presente, não cria linha.
        """
        linha, tag = self._linha_e_tag(endereco)
        if self._esta_na_cache(linha, tag):
            self.dado[linha] = valor & 0xFFFF

    def escrever(self, endereco, valor):
        """Write-through quando a cache é usada diretamente."""
        self.memoria.escrever(endereco, valor)
        self.atualizar_se_presente(endereco, valor)

    def get_state(self):
        """Tudo o que a interface precisa para desenhar a cache."""
        return {
            "nome": self.nome,
            "linhas": [
                {"valido": self.valido[i], "tag": self.tag[i], "dado": self.dado[i]}
                for i in range(self.num_linhas)
            ],
            "hits": self.hits,
            "misses": self.misses,
            "ultimo_acesso": self.ultimo_acesso,
        }