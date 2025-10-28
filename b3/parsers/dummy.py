from b3.parser import Parser


class DummyParser(Parser):
    gameName = "dummy"
    is_dummy = True

    def say(self, message):
        print(message)
