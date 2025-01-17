import random

random_numbers = [random.random() for _ in range(784)]
print(','.join(map(str, random_numbers)))