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

    N = 15; // change me to increase number of odd numbers

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