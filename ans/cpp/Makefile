SRC = rans.cpp
FLAGS = -std=c++20 -O2 -Wall -Werror
SANITIZE_FLAGS = -fsanitize=undefined -fsanitize=address

rans:
	g++ $(FLAGS) $(SRC) -o rans

clean:
	rm rans