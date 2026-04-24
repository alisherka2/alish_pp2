from classes.class_variables import Person

class Student(Person):
  def __init__(self, fname, lname):
    super().__init__(fname, lname)

class Student(Person):
  def __init__(self, fname, lname):
    Person.__init__(self, fname, lname)