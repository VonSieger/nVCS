from Data import Difference, Addition, Removal, Token, TextToken, popLocalQueue, popOtherQueue
from collections import deque

#Longest Common Subsequence-Algorithm implemented with memorizing
def LCS(A, B):
    AB = [0] * (len(A) +1)
    for x in range(len(AB)):
        AB[x] = [0] * (len(B) +1)

    for row in range(1, len(AB)):
        for column in range(1, len(AB[row])):
            if A[row -1] == B[column -1]:
                AB[row][column] = AB[row -1][column -1] +1
            else:
                AB[row][column] = max(AB[row -1][column], AB[row][column -1])

    #go backwards through table, to find subSequence
    subSequence = list()
    x = len(A)
    y = len(B)
    while AB[x][y] != 0:
        if AB[x][y] == AB[x-1][y]:
            x -= 1
        elif AB[x][y] == AB[x][y -1]:
            y -= 1
        else:
            subSequence.append(A[x -1])#-1 because of 0s in table
            x -= 1
            y -= 1

    subSequence.reverse()
    return subSequence

def makeDifference(commit, base, lcs):

    result = list()

    commitIndex = 0
    baseIndex = 0
    lcsIndex = 0

    while commitIndex < len(commit) and baseIndex < len(base) and lcsIndex < len(lcs):
        #print(commit[commitIndex].content)
        #print(lcs[lcsIndex].content)
        #print(base[baseIndex].content)
        if commit[commitIndex] == lcs[lcsIndex] and base[baseIndex] == lcs[lcsIndex]:
            result.append(commit[commitIndex])
            commitIndex += 1
            baseIndex += 1
            lcsIndex += 1
        elif not commit[commitIndex] == lcs[lcsIndex]:
            result.append(Addition(commit[commitIndex]))
            commitIndex += 1
        else:
            result.append(Removal(base[baseIndex]))
            baseIndex += 1
        #print(str(commitIndex) + "<" + str(len(commit)) + " and " + str(baseIndex) + "<" + str(len(base)) + " and " + str(lcsIndex) + "<" + str(len(lcs)))

    while baseIndex < len(base):
        result.append(Removal(base[baseIndex]))
        baseIndex += 1

    while commitIndex < len(commit):
        result.append(Addition(commit[commitIndex]))
        commitIndex += 1

    return result

def threeWayMerge(local, other, base):

    localDiff = deque(makeDifference(local, base, LCS(local, base)))
    otherDiff = deque(makeDifference(other, base, LCS(other, base)))

    merged = list()
    try:
        curLocal = localDiff.popleft()
    except IndexError:
        curLocal = None
    try:
        curOther = otherDiff.popleft()
    except IndexError:
        curOther = None
    state = (localDiff, otherDiff, curLocal, curOther)

    while state[2] is not None and state[3] is not None:
        result = state[2].compare(state[2], state[3])
        if result[0] is not None:
            merged.append(result[0])
        state = result[1](state)

    while state[2] is not None:
        if isinstance(state[2], Difference):
            merged.append(state[2].compare(state[2], Token(""))[0])
        else:
            merged.append(state[2])
        state = popLocalQueue(state)

    while state[3] is not None:
        if isinstance(state[3], Difference):
            merged.append(state[3].compare(state[3], Token(""))[0])
        else:
            merged.append(state[3])
        state = popOtherQueue(state)

    return merged
