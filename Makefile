CXXFLAGS := $(shell libpng-config --cflags)
LDFLAGS := $(shell libpng-config --ldflags)


CXXFLAGS += -std=c++11
diff: imgdiff.o
	$(CXX) -o $@ $^ $(LDFLAGS)

imgdiff.o: imgdiff.cpp
	$(CXX) -c $< $(CXXFLAGS)