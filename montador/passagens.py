from montador.leitor import separa_linha
from montador.checar_erros import ErroDeMontagem
from montador.instrucoes import (INSTRUCOES, OPERANDO_12_BITS, OPERANDO_8_BITS, OPERANDO_NENHUM,)
import re

#instrucoes cujo operando e um rotulo
desvios = {"JPOS", "JZER", "JUMP", "JNEG", "JNZE", "CALL"}

LIMITES_OPERANDO = {
    OPERANDO_12_BITS: (0, 4095),
    OPERANDO_8_BITS: (0, 255),
}

NOME_VALIDO = re.compile(r"[A-Z_][A-Z0-9_]*")

#o nome deve seguir o padrao
def nome_valido(nome):
    return NOME_VALIDO.fullmatch(nome) is not None

#confere se tem algum erro na estrutura da linha e envia mensagem se houver
def conferir_instrucao(numero, instrucao, operandos):

    if instrucao not in INSTRUCOES:
        raise ErroDeMontagem(numero, f"instrução desconhecida '{instrucao}'")

    _, tipo = INSTRUCOES[instrucao]

    if tipo == OPERANDO_NENHUM and operandos is not None:
        raise ErroDeMontagem(numero, f"{instrucao} não aceita operando")
    if tipo != OPERANDO_NENHUM and operandos is None:
        raise ErroDeMontagem(numero, f"{instrucao} precisa de operando")
    if operandos is not None and " " in operandos:
        raise ErroDeMontagem(numero, f"operando a mais em {instrucao}")

#1a passagem, descobre endereco de cada rotulo e confere a estrutura da linha
def anotagem_enderecos(linhas):

    #end da proxima instrucao
    contador = 0
    rotulos = {}

    for numero, linha in enumerate(linhas, start=1):

        rotulo, instrucao, operandos = separa_linha(linha)
    
        if rotulo is not None:
            if not nome_valido(rotulo):
                raise ErroDeMontagem(numero, f"nome inválido '{rotulo}'")
            if rotulo in rotulos:
                raise ErroDeMontagem(numero, f"rótulo '{rotulo}' já foi definido")
            rotulos[rotulo] = contador

        if instrucao:
            conferir_instrucao(numero, instrucao, operandos)
            contador += 1

    return rotulos, contador

#2a passagem, monta a palavra de 16 bits
def monta_endereco(linhas, rotulos, total):

    palavras = []
    variaveis = {}
    #1o endereco livre depois do codigo
    prox_endereco = total

    for numero, linha in enumerate(linhas, start=1):

        rotulo, instrucao, operandos = separa_linha(linha)

        if instrucao:

            base, tipo = INSTRUCOES[instrucao]

            if tipo == OPERANDO_NENHUM:
                operando = 0

            else:
                try:
                    #operando e um numero
                    operando = int(operandos)
                except ValueError:
                    if not nome_valido(operandos):
                        raise ErroDeMontagem(numero, f"nome inválido '{operandos}'")
                    if instrucao in desvios:
                        #operando e um rotulo
                        if operandos not in rotulos: raise ...
                        operando = rotulos[operandos]
                    else:
                        #operando e uma variavel
                        if operandos not in variaveis:
                            variaveis[operandos] = prox_endereco
                            prox_endereco += 1
                        operando = variaveis[operandos]

                minimo, maximo = LIMITES_OPERANDO[tipo]
                if not minimo <= operando <= maximo:
                    raise ErroDeMontagem(
                        numero,
                        f"operando {operando} não cabe em {tipo} bits "
                        f"(de {minimo} a {maximo})",
                    )

            palavras.append(base | operando)

    return palavras, variaveis
