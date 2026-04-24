from classes.init_method import Person

class Student(Person):
  def __init__(self, fname, lname):
    Person.__init__(self, fname, lname)