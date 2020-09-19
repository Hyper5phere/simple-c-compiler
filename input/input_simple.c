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