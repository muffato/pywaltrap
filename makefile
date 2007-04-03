CC = g++
PYTHON_INCLUDEDIR = /usr/include/python2.3
CFLAGS = -Wall -O3 -fPIC
LDFLAGS = -shared

all : walktrap pywalktrap.so

walktrap : walktrap.o communities.o graph.o heap.o
	$(CC) -o $@ $^

pywalktrap.so : pywalktrap.o communities.o graph.o heap.o
	$(CC) -o $@ $^ $(LDFLAGS)

py%.o : py%.cpp
	$(CC) -c $< $(CFLAGS) -I$(PYTHON_INCLUDEDIR)

%.o : %.cpp
	$(CC) -c $< $(CFLAGS)
clean :
	rm *.o

moreclean :
	rm *.o pywalktrap.so walktrap

