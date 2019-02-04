from hashlib import md5
from collections import deque


def bytesToInt(bytes):
    result = 0
    for b in bytes:
        result = result * 256 + int(b)
    return b

def popLocalQueue(queueTuple):
    try:
        curLocal = queueTuple[0].popleft()
    except IndexError:
        return (queueTuple[0], queueTuple[1], None, queueTuple[3])

    return (queueTuple[0], queueTuple[1], curLocal, queueTuple[3])

def popOtherQueue(queueTuple):
    try:
        curOther = queueTuple[1].popleft()
    except IndexError:
        return (queueTuple[0], queueTuple[1], queueTuple[2], None)

    return(queueTuple[0], queueTuple[1], queueTuple[2], curOther)

def popBothQueues(queueTuple):
    try:
        curLocal = queueTuple[0].popleft()
    except IndexError:
        curLocal = None
    try:
        curOther = queueTuple[1].popleft()
    except IndexError:
        curOther = None

    return(queueTuple[0], queueTuple[1], curLocal, curOther)

class Token:
    def __init__(self, content):
        self.content = content

    def __eq__(self, obj):
        if isinstance(obj, self.__class__) and obj.content == self.content:
                return True
        return False

    def compare(self, local, other):
        if isinstance(local, Addition):
            if isinstance(other, Addition):
                if local.token == other.token:
                    return (local.token, popBothQueues)
                else:
                    return (Conflict(local.token, other.token), popBothQueues)
            elif isinstance(other, Removal):
                return(local.token, popLocalQueue)
            elif isinstance(other, Token):
                return(local.token, popLocalQueue)
        elif isinstance(local, Removal):
            if isinstance(other, Addition):
                return(other.token, popOtherQueue)
            elif isinstance(other, Removal):
                return(None, popBothQueues)
            elif isinstance(other, Token):
                return(None, popBothQueues)
        elif isinstance(local, Token):
            if isinstance(other, Addition):
                return(other.token, popOtherQueue)
            elif isinstance(other, Removal):
                return(None, popBothQueues)
            elif isinstance(other, Token):
                return(local, popBothQueues)


class TextToken(Token):
    pass

class FileToken(Token):
    def __init__(self, relativePath, fileSystem):
        self.content = relativePath
        self.fileSystem = fileSystem
        tokens = fileSystem.readFile(relativePath)
        if(tokens is not None):
            md5HashGenerator = md5()
            for token in tokens:
                md5HashGenerator.update(bytes(token.content, "utf-8"))
            self.hashInt = bytesToInt(md5HashGenerator.digest())

#    def __eq__(self, obj):
#        if super().__eq__(obj):
#            return obj.hashInt == self.hashInt
#        return False

    def compare(self, local, other):
        if isinstance(local, Addition):
            if isinstance(other, Addition):
                if(other == local):
                    return(local, popBothQueues)
                elif(other.token.content == local.token.content):
                    return (Conflict(local, other, "A file with the same name, but different content, was added to both directories."), popBothQueues)
                return(local, popLocalQueue)
            elif isinstance(other, Removal):
                return(local, popLocalQueue)
            elif isinstance(other, Token):
                return(local, popLocalQueue)
        elif isinstance(local, Removal):
            if isinstance(other, Addition):
                return(other, popOtherQueue)
            elif isinstance(other, Removal):
                return(local, popBothQueues)
            elif isinstance(other, Token):
                return(local, popBothQueues)
        elif isinstance(local, Token):
            if isinstance(other, Addition):
                return(other, popOtherQueue)
            elif isinstance(other, Removal):
                return(other, popOtherQueue)
            elif isinstance(other, Token):
                return(local, popBothQueues)

class Difference:
    def __init__(self, token):
        self.token = token

    def __eq__(self, obj):
        if isinstance(obj, self.__class__) and obj.token == self.token:
            return True
        return False

    def compare(self, local, other):
        return self.token.compare(local, other)

class Addition(Difference):
    pass

class Removal(Difference):
    pass

class Conflict():
    def __init__(self, tokenLocal, tokenOther, errMsg=""):
        self.tokenLocal = tokenLocal
        self.tokenOther = tokenOther
        self.errMsg = errMsg

class FileConflict(Conflict):
    def __init__(self, local, other):
        self.local = local
        self.other = other
