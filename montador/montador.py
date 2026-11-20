from montador.passagens import anotagem_enderecos, monta_endereco

"""recebe o texto do programa e devolve: lista de palavras de 16 bits, endereco de cada rotulo e endereco de cada variável"""

def montar(entrada):

    linhas = entrada.splitlines()

    rotulos, total = anotagem_enderecos(linhas)
    palavras, variaveis = monta_endereco(linhas, rotulos, total)

    return palavras, rotulos, variaveis
