def digits_of(number_sequence):
    return [int(digit) for digit in str(number_sequence)]


def luhn_checksum(card_number):
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = 0
    checksum += sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return True if checksum % 10 == 0 else False
