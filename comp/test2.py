import complexity

bub ="""
import random
s = [random.randint(0, n) for _ in range(n)]
def bubble_sort(seq):
    changed = True
    while changed:
        changed = False
        for i in range(len(seq) - 1):
            if seq[i] > seq[i+1]:
                seq[i], seq[i+1] = seq[i+1], seq[i]
                changed = True
    return seq
"""

if __name__ == '__main__':
	cc = complexity.ComputeComplexity(name="n", setup=bub, execute='bubble_sort(s)')
	cc.compute(timeout=10)
