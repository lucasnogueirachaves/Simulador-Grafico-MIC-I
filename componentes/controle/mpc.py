from via_de_dados.registradores.registrador import Registrador

class MicroprogramCounter(Registrador):
    def __init__(self, identificador):
        super().__init__(identificador, 8)
    