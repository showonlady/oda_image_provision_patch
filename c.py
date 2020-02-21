#!/usr/bin/env python
#coding utf-8


#tree_t = [[7],[3,8],[8,1,0], [2,7,4,4],[4,5,2,6,5]]
input = "7\n3 8\n8 1 0\n2 7 4 4\n4 5 2 6 5"
input = input.split("\n")
input = [i.split() for i in input]
print input
tree_t = [map(int, i) for i in input]
print tree_t




def fun(a, b):
    c = []
    for i in range (len (b)):
        sum1 = a[i] + b[i]
        sum2 = a[i + 1] + b[i]
        c.append (max (sum1, sum2))
    return c



def main():

    for i in tree_t:
        for j in i:
            if j < 0 or j > 99:
                return None

    if len (tree_t) == 1:
        print tree_t[0]
    elif len (tree_t) == 0:
        return 0
    elif len (tree_t) > 100:
        return None
    else:
        a = tree_t[-1]
        j = len(tree_t)
        while j > 1:
            b = tree_t[j-2]
            j = j -1
            # print b
            # print a
            a = fun(a, b)
    print a[0]

main()

# c = [[7],[3,8],[8,1,0], [2,7,4,4],[4,5,2,6,5]]
# a = c[-1]
# j = len(c)
# while j > 1:
#     b = c[j-2]
#     j = j -1
#     # print b
#     # print a
#     a = fun(a, b)
# print a

# tree = input.split ("\n")
# tree_t = []
# for i in tree:
#     tree_t.append(i.split())
# print tree_t
# for i in range(len(tree_t)):
#     for j in tree_t[i]:
#         print j