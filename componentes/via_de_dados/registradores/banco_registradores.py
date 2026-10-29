from registrador import Registrador
from registrador_constante import RegistradorConstante

class BancoRegistradores:
    def __init__(self):
        self.registradores = [
            Registrador("PC"), Registrador("AC"), Registrador("SP"),
            Registrador("IR"), Registrador("TIR"),
            RegistradorConstante("0", 0),
            RegistradorConstante("+1", 1),
            RegistradorConstante("-1", -1),
            RegistradorConstante("AMASK", 0x0FFF),
            RegistradorConstante("SMASK", 0x00FF),
            Registrador("A"), Registrador("B"), Registrador("C"),
            Registrador("D"), Registrador("E"), Registrador("F"),
        ]

    def ler(self, endereco):
        return self.registradores[endereco].ler()

    def gravar(self, endereco, valor):
        self.registradores[endereco].gravar(valor)