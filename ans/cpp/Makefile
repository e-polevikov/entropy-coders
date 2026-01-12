SRC = rans.cpp
FLAGS = -std=c++20 -O2 -Wall -Werror
SANITIZE_FLAGS = -fsanitize=undefined

rans:
	g++ $(FLAGS) $(SANITIZE_FLAGS) $(SRC) -o rans

clean:
	rm rans