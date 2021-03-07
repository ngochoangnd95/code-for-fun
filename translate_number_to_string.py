import math


level_join_words = ["", "nghìn", "triệu", "tỉ"]
join_words = ["", "mươi", "trăm"]
digit_words = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
ten_join_word = "mười"
change_join_word = "lẻ"
spec_one = "mốt"
spec_five = "lăm"
spec_four = "tư"


def get_input():
    number_input = input("Nhập số cần đọc: ")
    assert number_input.isnumeric(), "Đây không phải là số."
    return number_input
    
    
def join_up(*words):
    return ' '.join(filter(lambda w: w, words))


def simplify(string):
    result = string
    # "mươi không" -> "mươi"
    result = result.replace(join_words[1] + ' ' + digit_words[0], join_words[1])
    # "không mươi" -> "lẻ"
    result = result.replace(digit_words[0] + ' ' + join_words[1], change_join_word)
    # "không trăm lẻ" -> "lẻ"
    result = result.replace(digit_words[0] + ' ' + join_words[2] + ' ' + change_join_word, change_join_word)
    # "trăm lẻ" -> "trăm"
    result = result.replace(join_words[2] + ' ' + change_join_word, join_words[2])
    # "một mươi" -> "mười"
    result = result.replace(digit_words[1] + ' ' + join_words[1], ten_join_word)
    # "mươi một" -> "mươi mốt"
    result = result.replace(join_words[1] + ' ' + digit_words[1], join_words[1] + ' ' + spec_one)
    # "mươi bốn" -> "mươi tư"
    result = result.replace(join_words[1] + ' ' + digit_words[4], join_words[1] + ' ' + spec_four)
    # "mươi năm" -> "mươi lăm"
    result = result.replace(join_words[1] + ' ' + digit_words[5], join_words[1] + ' ' + spec_five)
    return result

 
def get_trio_string(trio):
    result = ''
    length = len(trio)
    for i in range(length):
        digit = int(trio[length - 1 - i])
        result = join_up(digit_words[digit], join_words[i], result)
    return simplify(result)

    
def get_number_string(number_input):
    length = len(number_input)
    level = math.ceil(length / 3)
    result = ''
    for lev in range(level):
        start = length - 3 * (lev + 1)
        if start < 0:
            start = 0
        end = length - 3 * lev
        trio = number_input[start:end]
        if int(trio) == 0:
            continue
        complex_level_join_word = ''
        leap_level = lev
        while leap_level > 3:
            complex_level_join_word = join_up(level_join_words[3], complex_level_join_word)
            leap_level -= 3
        complex_level_join_word = join_up(level_join_words[leap_level], complex_level_join_word)
        result = join_up(get_trio_string(trio), complex_level_join_word, result)
    return result


if __name__ == "__main__":
    number_input = get_input()
    print(get_number_string(number_input))
