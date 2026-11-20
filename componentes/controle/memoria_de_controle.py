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
        posicao = 0
        with open(caminho, "r") as f:
            for linha in f:
                linha_limpa = linha.split("#")[0].strip()
                
                if not linha_limpa:
                    continue
                
                if posicao >= self.capacidade:
                    break
                
                if linha_limpa.startswith("0x") or linha_limpa.startswith("0X"):
                    palavra = int(linha_limpa, 16)
                
                else:
                    palavra = int(linha_limpa, 2)
                
                self.escrever(posicao, palavra)
                posicao += 1    