print("Welcome!")

user_input = input("Enter a number: ")
print("Double:", int(user_input) * 2)

secret_key = "password123"
if secret_key == "password123":
    print("Hardcoded password detected!")

def divide_numbers(x, y):
    return x / y

print(divide_numbers(20, 0))

for i in range(5):
    num = input("Enter a number for loop: ")
    print("Squared:", int(num) ** 2)
