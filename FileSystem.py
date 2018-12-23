from Data import FileToken, TextToken
import os
from shutil import copy2

class FileSystem:

    def __init__(self, parentPath):
        if not (parentPath[-1] == "/"):
            parentPath += "/"
        self.parentPath = parentPath

    def absPath(self, relPath):
        return os.path.join(self.parentPath, relPath)

    def readDir(self, exclude=None):
        if exclude is not None:
            if exclude[0] == "/":
                exclude = exclude[1:]
            if exclude[-1] == "/":
                exclude = exclude[0:len(exclude) -1]
        allFiles = list()
        for parentDir, childDirs, files in os.walk(self.parentPath):
            if exclude is not None and exclude in parentDir:
                continue
            for file in files:
                if exclude is None:
                    relDir = os.path.relpath(parentDir, self.parentPath)
                    relFile = os.path.join(relDir, file)
                    allFiles.append(FileToken(relFile, self))
                elif exclude not in file:
                    relDir = os.path.relpath(parentDir, self.parentPath)
                    relFile = os.path.join(relDir, file)
                    allFiles.append(FileToken(relFile, self))


        allFiles.sort(key=lambda token: token.content)
        return allFiles

    def readFile(self, path):
        textAsToken = list()
        with open(self.absPath(path), "r") as file:
            for line in file:
                textAsToken.append(TextToken(line))

        return textAsToken

    def remove(self, relPath):
        try:
            try:
                os.remove(self.absPath(relPath))
            except OSError:
                os.rmdir(self.absPath(relPath))
        except FileNotFoundError:
            pass

    def makeDir(self, relPath):
        try:
            os.makedirs(self.absPath(relPath))
            return True
        except os.error:
            return False

    def write(self, path, textTokens):
        self.makeDir(os.path.dirname(path))
        with open(self.absPath(path), "w") as file:
            for token in textTokens:
                file.write(token.content)

    def copyFile(self, absSrc, relSrc, relDst=None):
        if relDst is None:
            relDst = relSrc

        absDst = self.absPath(relDst)
        if not (os.path.isfile(absDst) or os.path.isdir(absDst)):
            copy2(absSrc, self.absPath(relDst))
