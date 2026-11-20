"""le uma linha de assembly, remove comentarios e separa rotulo, instrucao e operando"""

def separa_linha(linha):

    #primeiro: tira os comentarios, espacos extras e coloca tudo em maisculo
    linha = linha.partition(";")[0]
    linha = linha.strip().upper()

    #linha vazia ou so tinha comentario
    if not linha:
        return None, None, None

    #separa o rotulo (se houver)
    inicio, meio, final = linha.partition(":")

    #checa se ha rotulo
    if meio:
        rotulo = inicio.strip()
        resto = final
    else:
        rotulo = None
        resto = linha

    #divide instrucao de operando
    separacao = resto.split()
    if not separacao:
        return rotulo, None, None

    #primeira palavra e a instrucao e o que sobra operando
    instrucao = separacao[0]

    if len(separacao) > 1:
        #para checar depois de tem operando a mais
        operando = " ".join(separacao[1:])
    else:
        operando = None

    return rotulo, instrucao, operando
