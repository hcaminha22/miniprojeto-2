import re


def solicitar_nome(mensagem="Digite o nome do cliente: "):
    while True:
        nome = input(mensagem).strip()

        caracteres_validos = all(
            caractere.isalpha() or caractere in " -'"
            for caractere in nome
        )
        quantidade_letras = sum(
            caractere.isalpha() for caractere in nome
        )

        if len(nome) >= 3 and caracteres_validos and quantidade_letras >= 2:
            return nome

        print("Erro: informe um nome válido, sem números ou símbolos especiais.")


def solicitar_cpf(mensagem="Digite o CPF do cliente: "):
    while True:
        cpf_informado = input(mensagem).strip()

        formato_valido = re.fullmatch(
            r"(?:\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2})",
            cpf_informado
        )
        cpf = re.sub(r"\D", "", cpf_informado)

        if formato_valido and cpf != cpf[0] * 11:
            return cpf

        print("Erro: informe um CPF válido com 11 dígitos.")


def solicitar_numero_conta():
    while True:
        numero = input("Digite o número da conta: ").strip()

        if numero.isdigit() and int(numero) > 0:
            return int(numero)

        print("Erro: o número da conta deve conter somente números.")


def solicitar_valor(mensagem):
    from entidades.conta import Conta
    while True:
        try:
            return Conta.validar_valor(input(mensagem))
        except ValueError as erro:
            print(f"Erro: {erro}")
