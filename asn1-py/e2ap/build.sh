#!/bin/bash
gcc -c -fPIC -I include src/*.c wrapper.c
gcc *.o -shared -o libasn1.so
rm *.o
