NUM_BITS = 16
MASCARA = (1 << NUM_BITS) - 1 

def limitar_16_bits(valor):
    return valor & MASCARA

def eh_negativo(valor):
    sinal = (valor >> (NUM_BITS - 1)) & 1
    return sinal


def ula(a, b, op):

    if op == 0:
        resultado = a + b
    elif op == 1:
        resultado = a & b
    elif op == 2:
        resultado = a
    elif op == 3:
        resultado = ~a
    else:
        raise ValueError("Operação inválida")

    resultado = limitar_16_bits(resultado)

    n = eh_negativo(resultado)
    z = 1 if resultado == 0 else 0

    return resultado, n, z
