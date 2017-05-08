import complexity

qsort1 ="""
import random
s = [random.randint(0, n) for _ in range(n)]
def qsort(L):
    return (qsort([y for y in L[1:] if y <  L[0]]) + 
            L[:1] + 
            qsort([y for y in L[1:] if y >= L[0]])) if len(L) > 1 else L
"""

if __name__ == '__main__':
    cc = complexity.ComputeComplexity(name="n",  setup=qsort1, execute='qsort(s)')
    cc.compute(timeout=10)
