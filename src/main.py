def hello(name: str, age: int) -> str:
    result1: str = "My name is " + name + ".\n"
    result2: str = "I am " + str(age) + " years old."
    return result1 + result2


def test():
    bbb = "aaa"
    ccc = "ddd"
    print(bbb + ccc)


result: str
result = hello(name="Otao", age=23)
print(result)
