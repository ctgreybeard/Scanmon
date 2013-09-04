#!/sw/bin/python3

from scanner import Scanner

S=Scanner()

print("we have a scanner: ", S)
print('Is it open?', S.isOpen());

print('Doing discovery ... OK?', S.discover())

