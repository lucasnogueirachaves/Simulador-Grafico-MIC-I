class MemoriaDeControle:
    
    def __init__(self):
        self.capacidade = 256
        self._memoria = [0] * self.capacidade
    
    def ler(self, endereco):
        addr = endereco & 0xFF
        return self._memoria[addr]
    
    def escrever(self, endereco, microinstrucao):
        addr = endereco & 0xFF
        self._memoria[addr] = microinstrucao & 0xFFFFFFFF
        
    def carregar_microprograma(self, microinstrucoes: list[int]):
        for i, palavra in enumerate(microinstrucoes):
            if i < self.capacidade:
                self.escrever(i, palavra)
                
    def carregar_microprograma_arquivo(self, caminho: str):
        with open(caminho, "r") as f:
            linhas = [linha.strip() for linha in f]
            for i, linha in enumerate(linhas):
                if i >= self.capacidade:
                    break
                if linha[0] == "0x" or linha[0] == "0X":
                    palavra = int(linha, 16)
                else: 
                    palavra = int(linha, 2)
                self.escrever(i, palavra)
    