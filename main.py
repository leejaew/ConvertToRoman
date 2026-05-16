# create a dictionary with the Roman numeral values
roman_numerals = {
    1000: "M",
    900: "CM",
    500: "D",
    400: "CD",
    100: "C",
    90: "XC",
    50: "L",
    40: "XL",
    10: "X",
    9: "IX",
    5: "V",
    4: "IV",
    1: "I"
}

# prompt the user to enter a number
number = int(input("Enter a number: "))

# initialize the result string
result = ""

# iterate through the dictionary keys in descending order
for value in sorted(roman_numerals.keys(), reverse=True):
    # while the number is greater than or equal to the current key
    while number >= value:
        # append the corresponding Roman numeral to the result string
        result += roman_numerals[value]
        # subtract the current key from the number
        number -= value

# print the result
print("Roman numeral:", result)
