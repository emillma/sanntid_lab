class A:
    def __init__(self):
        self.data = 2

    def add
    def __iadd__(self, other):
        self.data += other

    def __str__(self):
        return str(self.data)

a = A()
print(a)
a =+ 4
print(a)