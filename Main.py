from os import getcwd
from os import path
from FileSystem import FileSystem
from Comparison import threeWayMerge
from Data import Token, TextToken, Conflict, Addition, Removal
import sys
import getopt

NOT_A_NVCS_DIRECTORY = "This is no directory initialized for nVCS.\nTry 'nvcs --help' for more information."
HELP = """Usage: nvcs [command][path]
Merge two directories based on a third base directory.\n
Commands:
\tinit [/path/to/otherDir]\tInitialize current directory for further nVCS use.
\t\tCreates .nvcs/, .nvcs/base/ and .nvcs/config
\tmerge\tMerge this(local) directory with the other directory(described in .nvcs/config)
\t\t, based on the .nvcs/base directory"""
CONFIG_TEXT="TARGET_DIR=<target_dir>"

hiddenDirName = ".nvcs/"
localDir = None
otherDir = None
baseDir = None
localPath = None
#init defines the target path
arguments = {"init": None, "merge": False, "help": False}

class ArgumentException(Exception):
    def __init__(self, arg):
        self.args = arg

def allocate():
    global localDir
    global otherDir
    global baseDir
    global localPath

    localPath = getcwd()

    if not path.isdir(path.join(localPath, hiddenDirName)):
        print(NOT_A_NVCS_DIRECTORY)
        sys.exit(1)
    if not path.isfile(path.join(localPath, hiddenDirName, "config")):
        print(NOT_A_NVCS_DIRECTORY)
        sys.exit(1)
    if not path.isdir(path.join(localPath, hiddenDirName, "base")):
        print(NOT_A_NVCS_DIRECTORY)
        sys.exit(1)

    localDir = FileSystem(localPath)
    configFile = localDir.readFile(path.join(hiddenDirName, "config"))

    for line in configFile:
        if "TARGET_DIR" in line.content:
            otherDirPath = line.content.split("=")[1].replace("\n", "")

    otherDir = FileSystem(otherDirPath)
    baseDir = FileSystem(path.join(localPath, hiddenDirName, "base"))

    return(localDir, otherDir, baseDir)

def parseArguments(args):
    global arguments
    try:
        opts, args = getopt.getopt(args, "h", ["init=", "merge", "help"])
    except getopt.GetoptError as e:
        raise ArgumentException(("Invalid argument syntax", e.args[0]))

    if len(opts) == 0:
        raise ArgumentException(("No arguments given", ""))

    for opt, arg in opts:
        if opt == "--merge":
            arguments["merge"] = True
        elif opt == "--init":
            if(path.isdir(arg)):
                arguments["init"] = arg
            else:
                raise ArgumentException(("No valid path for a directory", arg))
        elif opt in ["-h", "--help"]:
            arguments["help"] = True

def initialize(targetPath):
    localPath = getcwd()
    tmpFileSystem = FileSystem(localPath)
    if not tmpFileSystem.makeDir(hiddenDirName):
        print("Fatal Error: Could not create " + path.join(localPath, hiddenDirName))
        sys.exit(1)
    if not tmpFileSystem.makeDir(path.join(hiddenDirName, "base/")):
        print("Fatal Error: Could not create " + path.join(localPath, hiddenDirName, "base/"))
        sys.exit(1)
    configToken = TextToken(CONFIG_TEXT.replace("<target_dir>", targetPath))
    tmpFileSystem.write(path.join(hiddenDirName, "config"), [configToken])

def commonList(listA, listB, key=lambda obj: obj):
    setA = set(listA)
    setB = set(listB)

    return list(setA & setB)

if __name__ == "__main__":
    try:
        parseArguments(sys.argv[1:])
    except ArgumentException as e:
        print(e.args[0] + ": " + e.args[1])
        print("Try 'nvcs --help' for more information.")
        sys.exit(1)
    if arguments["help"] == True:
        print(HELP)
        sys.exit(0)
    if arguments["init"] is not None:
        initialize(arguments["init"])
    if arguments["merge"] == False:
        sys.exit(0)
    allocate()

    dirResult = threeWayMerge(localDir.readDir(exclude=hiddenDirName), otherDir.readDir(), baseDir.readDir())
    for result in dirResult:
        if isinstance(result, Token):
            continue
        elif (result.token.binary):
            continue
        elif isinstance(result, Conflict):
            print("There is a error for these two files:")
            print("\t(1)" + result.tokenLocal.content)
            print("\t(2)" + result.tokenOther.content)
            print(result.errMsg)
            print("Options:\n\t(1)Keep file 1 and overwrite 2\n\t(2)Keep file 2 and overwrite 1\n\t(3)Exit nVCS and resolve problem manually")
            fileToKeep = int(input("\n Which file do you want to keep?"))
            if fileToKeep == 1:
                otherDir.remove(result.tokenLocal.content)
                baseDir.remove(result.tokenLocal.content)
                otherDir.copyFile(result.tokenLocal.fileSystem, result.tokenLocal.content)
                baseDir.copyFile(result.tokenLocal.fileSystem, result.tokenLocal.content)
            elif fileToKeep == 2:
                localDir.remove(result.tokenOther.content)
                baseDir.remove(result.tokenOther.content)
                localDir.copyFile(result.tokenOther.fileSystem, result.tokenOther.content)
                baseDir.copyFile(result.tokenOther.fileSystem, result.tokenOther.content)
            else:
                system.exit(0)
        else:
            token = result.token
            absPath = token.fileSystem.absPath(token.content)
            if isinstance(result, Addition):
                localDir.copyFile(absPath, token.content)
                otherDir.copyFile(absPath, token.content)
                baseDir.copyFile(absPath, token.content)
            elif isinstance(result, Removal):
                localDir.remove(token.content)
                otherDir.remove(token.content)
                baseDir.remove(token.content)

    #remove files, which were not copied before
    filePaths = commonList(localDir.readDir(exclude=hiddenDirName), otherDir.readDir())

    for filePath in filePaths:
        localTokenList = localDir.readFile(filePath.content)
        otherTokenList = otherDir.readFile(filePath.content)
        baseTokenList = baseDir.readFile(filePath.content)

        if(localTokenList is None or otherTokenList is None or baseTokenList is None):
            continue

        if localTokenList == otherTokenList:
            if otherTokenList == baseTokenList:
                continue
            else:
                baseDir.write(filePath.content, localTokenList)
        else:
            merged = threeWayMerge(localTokenList, otherTokenList, baseTokenList)
            for token in merged:
                if isinstance(token, Conflict):
                    ## TODO: improve Conflict handling
                    print("There is a merge conflict in the file " + filePath)
                    print("Absolute paths:\n\t(1) " + localDir.absPath(filePath) + "\n\t(2) " + otherDir.absPath(filePath))
                    continue
            localDir.write(filePath.content, merged)
            otherDir.write(filePath.content, merged)
            baseDir.write(filePath.content, merged)


def copy(srcFileSystem, dstFileSystem, relPath):
    absSrc = path.join(srcFileSystem.parentPath, relPath)
    dstFileSystem.copy(absSrc, relPath)
