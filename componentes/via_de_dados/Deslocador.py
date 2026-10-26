from componentes.via_de_dados.ULA import limitar_16_bits

class Deslocador:

    def __init__(self):
        self.entrada = 0
        self.sh = 0
        self.resultado = 0

    def execucao(self, valor, sh):
        if sh == 0:
            resultado = valor
        elif sh == 1: #esquerda
            resultado = valor << 1
        elif sh == 2: #direita
            resultado = valor >> 1

        else:
            raise ValueError("Operação de deslocamento inválida.")

        resultado = limitar_16_bits(resultado)

        self.entrada = valor
        self.sh = sh
        self.resultado = resultado

        return self.resultado
