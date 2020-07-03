# C-minus Compiler written in Python

C-minus is a subset of C programming language with limited capabilities. Currently it supports only integer typed variables.

## Requirements

Make sure Python 3.6 or newer interpreter is installed on your system. Then install the ``anytree`` package with pip
```bash

pip install anytree
```

## Installation and Testing

For testing there is a simple test program that prints the 5 first odd numbers
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
One could implement support for
- arrays
- recursion
- string types