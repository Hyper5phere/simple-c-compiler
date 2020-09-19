# Simple C Compiler written in Python

Simple C Compiler supports a subset of C programming language. Most notably it has only integer typed variables. Nevertheless, it is a fully functional C compiler front-end for generating intermediate representation (IR) three address codes from a C source file. Also an interpreter for the three address "assembly" code is provided for all major platforms (Windows, Linux and Mac).

As the name hints, it is also simple to use! Only one python module needed to start using it!

## Requirements

Make sure Python 3.6 or newer interpreter is installed on your system. Then install the ``anytree`` package with pip
```bash

pip install anytree
```

## Installation and Testing

For testing the compiler here is a simple test program that prints the 5 first odd numbers
```c
/* 
 * Simple example source code
 * 
 * prints N odd numbers
 */

void main(void) {
    int i;
    int j;
    int m;
    int N;
    
    m = 0-1;
    i = 1;
    j = 1;

    N = 5; // change me to increase number of odd numbers

    while (i < N * 2 + 1) {
        j = m * j;
        if (j < 0) {
            output(i);
        } else {
            // do nothing
        }
        i = i + 1;
    }

}
```

To compile and run it, type
```bash
git clone https://github.com/Hyper5phere/c-minus-compiler.git
cd c-minus-compiler
python compiler.py input/input_simple.c --run
```

## Possible Future Improvements
Language support for
- arrays
- recursion
- string types