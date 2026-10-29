class Registrador:
    
    def __init__(self, identificador, largura=16):
        self.identificador = identificador
        self.largura = largura
        self.mascara = (1 << largura) - 1
        self.valor = 0
        self.ativo = False

    def gravar(self, valor):
        self.valor = valor & self.mascara 
        self.ativo = True

    def ler(self):
        self.ativo = True
        return self.valor

    def resetar(self):
        self.valor = 0
        self.ativo = False
    