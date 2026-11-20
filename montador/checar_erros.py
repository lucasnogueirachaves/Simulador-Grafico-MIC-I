"""para avisar de erros encontrados na entrada do usario que nao permitem a montagem"""

class ErroDeMontagem(Exception):

    def __init__(self, numero_linha, mensagem):
        super().__init__(f"linha {numero_linha}: {mensagem}")
        self.numero_linha = numero_linha
        self.mensagem = mensagem
