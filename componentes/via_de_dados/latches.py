class Latchs:


    def __init__(self):
        self.conteudo = 0       #inicializa o latch

    def carregar(self, valor):
        self.conteudo = valor      #atualiza o valor vindo do barramento

    def ler(self):
        return self.conteudo        #retorna o valor guardado

latch_a = Latchs()
latch_b = Latchs()