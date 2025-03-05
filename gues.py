import random
import inflect
p = inflect.engine()

def text_to_number(text):
    if text.isdigit():
        return int(text)
    else:
        return p.number_to_words(text)

def convert_input(user_input):
    if user_input.isdigit():
        return int(user_input)
    else:
        try:
            return int(text_to_number(user_input))
        except ValueError:
            return None
def main():
    number_to_guess = random.randint(1, 100)
    print("Adivinhe o número entre 1 e 100.")

    while True:
        user_input = input("Digite seu palpite: ")
        user_input = convert_input(user_input)
        if user_input is None:
            print("Entrada inválida. Por favor, digite um número inteiro.")
            continue

        user_input = int(user_input)
        if user_input < 1 or user_input > 100:
            print("Por favor, digite um número entre 1 e 100.")
            continue

        if user_input < number_to_guess:
            print("O número é maior.")
        elif user_input > number_to_guess:
            print("O número é menor.")
        else:
            print("Parabéns! Você acertou.")
            break

if __name__ == "__main__":
    main()