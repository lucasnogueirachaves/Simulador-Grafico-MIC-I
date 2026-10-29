from registrador import Registrador

class RegistradorConstante(Registrador):
    
    def __init__(self, identificador, constante, largura=16):
        super().__init__(identificador, largura)
        self.valor = constante & self.mascara

    def gravar(self, valor):
        pass                  

    def resetar(self):
        self.ativo = False 