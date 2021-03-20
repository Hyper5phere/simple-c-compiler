# Simple C Compiler written in Python

Simple C Compiler supports a subset of C programming language. Most notably it has only integer typed variables. Nevertheless, it is a fully functional C compiler front-end for generating intermediate representation (IR) three address codes from a C source file. Furthermore, an interpreter program [1] for the three address "assembly" code is provided for all major platforms (Windows, Linux and Mac) to execute the programs with ease.

As the name hints, it is also simple to use! Only one python module needed to start using it!

This compiler implementation is also part of a [blog post about designing and implementing compilers](https://medium.com/@pasi_pyrro/how-to-write-your-own-c-compiler-from-scratch-with-python-90ab84ffe071), you might wanna check it out!

## Requirements
All major operating systems (Windows, Linux and Mac) should be supported.

Make sure Python 3.6 or newer interpreter is installed on your system. Then install the ``anytree`` package with pip

```bash

pip install anytree
```

## Installation and Testing

For testing the compiler here is a simple test program that prints the 15 first odd numbers
```c
/* 
 * Simple example source code
 * 
 * prints N odd numbers
 */

void main(void) {
    /* all variables need to be declared first */
    int i;
    int j;
    int m;
    int N;
    
    /* ...and then assigned to */
    i = 1;
    j = 1;
    m = 0-1; // syntax only supports binary operations, this is how we get -1

    N = 15; // change me to increase number of odd numbers

    while (i < N * 2 + 1) {
        j = m * j;
        if (j < 0) {
            output(i);
        } else {
            // do nothing, the syntax does not support if without else :^)
        }
        i = i + 1;
    }
}
```

To compile and run it, type
```bash
git clone https://github.com/Hyper5phere/simple-c-compiler.git
cd simple-c-compiler
python compiler.py input/input_simple.c --run
```

To see all input arguments type
```bash
python compiler.py --help
```

All output of the compiler is stored in the ``./output`` folder and all the input examples can be found from ``./input`` folder. Additionally errors are logged in the ``./errors`` folder if ``--error-files`` input flag is used.


## Possible Future Improvements
Language support for
- arrays
- recursion
- string types
- nested functions (not really C though)

## References
[1] The interpreter program has been implemented by Romina Jafarian, at Computer Engineering Department of Sharif
University of Technology (Tehran) in Fall 2017.
