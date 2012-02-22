# $Id: enum.py 620 2010-08-05 10:55:36Z gnoel $

class Enum(object):
    elements = []
    symbol = ''
    id = 0
    
    def __init__(self, id=0, attributes={}):
        self.id = id
        for key in attributes:
            setattr(self, key, attributes[key])
    
    def addElement(self, name, attributes):
        element = Enum(len(self.elements), attributes)
        setattr(self, name, element)
        self.elements.append(element)
    
    def getElement(self, id):
        return self.elements[id]

    def getId(self):
        return self.id
    
    def getSymbol(self):
        return self.symbol
