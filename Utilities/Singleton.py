def Singleton(class_):
  instances = {}
  def getinstance(*args, **kwargs):
    if class_ not in instances:
        instances[class_] = class_(*args, **kwargs)
    return instances[class_]
  return getinstance

if __name__ == '__main__':
    @Singleton
    class TestClass:
      pass

    c1 = TestClass()
    c2 = TestClass()
    if id(c1) == id(c2):
        print(id(c1), "==", id(c2), ": ok")
    else:
        print(id(c1), "!=", id(c2), ": error")

