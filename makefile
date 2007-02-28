CC=g++
CFLAGS= -Wall -O3 -s -static -momit-leaf-frame-pointer -minline-all-stringops -march=pentium4 -mfpmath=sse -mmmx -msse -msse2

walktrap : walktrap.o communities.o graph.o heap.o
	$(CC) -o $@ $^ $(CFLAGS)

all : walktrap

%.o : %.cpp
	$(CC) -c $< $(CFLAGS) 
clean:
	rm *.o
	

