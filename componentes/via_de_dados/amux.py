class Amux:

    def __init__(self):
        pass

    def selecionar(self,sinal_controle, valor_latchA, valor_mbr):
        if sinal_controle == 0:
            return valor_latchA
        else:
            return valor_mbr