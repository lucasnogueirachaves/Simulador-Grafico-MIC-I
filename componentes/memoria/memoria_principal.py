class MemoriaPrincipal:
    """Memoria principal do MIC-1: uma lista de palavras de 16 bits."""

    def __init__(self, tamanho=4096):
        self.tamanho = tamanho
        self.dados = [0] * tamanho          

    def _verificar_endereco(self, endereco):
        if not 0 <= endereco < self.tamanho:
            raise IndexError(f"Endereco {endereco} fora da memoria (0 a {self.tamanho - 1})")

    def ler(self, endereco):
        self._verificar_endereco(endereco)
        return self.dados[endereco]

    def escrever(self, endereco, valor):
        self._verificar_endereco(endereco)
        self.dados[endereco] = valor & 0xFFFF   # corta para caber em 16 bits

    def carregar_programa(self, palavras, inicio=0):
        """Coloca na memoria a lista de palavras que sai do montador."""
        for i, palavra in enumerate(palavras):
            self.escrever(inicio + i, palavra)

    def reset(self):
        self.dados = [0] * self.tamanho