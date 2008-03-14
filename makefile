CC = g++
PYTHON_INCLUDEDIR = /usr/include/python2.5
CFLAGS = -W -Wall -O3 -ftree-vectorize -fomit-frame-pointer
LDFLAGS = -shared -fPIC

all : walktrap _walktrap.so

walktrap : walktrap.o communities.o graph.o heap.o
	$(CC) -o $@ $^

_walktrap.so : pywalktrap.o communities.o graph.o heap.o
	$(CC) -o $@ $^ $(LDFLAGS)

py%.o : py%.cpp
	$(CC) -c $< $(CFLAGS) -I$(PYTHON_INCLUDEDIR)

%.o : %.cpp
	$(CC) -c $< $(CFLAGS)
clean :
	rm *.o *.pyo

moreclean :
	rm *.o *.pyo _walktrap.so walktrap

