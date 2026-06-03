
def PrintSomething(instance):
    print(instance.name)

class Student():
    def __init__(self,name):
        self.name = name
    def PrintSomething(instance):
        print(instance.name)
a = Student("Lyy")
a.PrintSomething()