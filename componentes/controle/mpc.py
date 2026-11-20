from via_de_dados.registradores.registrador import Registrador

class Mpc(Registrador):
    def __init__(self):
        super().__init__("mpc", 8)
    