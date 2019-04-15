* Write AST traverser so that we can introduce a new scope like below
```
while cond:
   xxx
```
to
```
while cond:
   with scope('while_1'):
       xxx
```
The idea is to do this with every control structure so with each scope numbered so that we effectively have subroutine like entry and exit for control flow. The scope will simply increment the method number, and set the previous method when it exits. This allows us to capture optional and repeating parts of the grammar.
