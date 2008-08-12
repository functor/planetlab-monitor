CC = g++
LIBTOOL = libtool
ARCH := $(shell uname -m | sed 's/i.86/i386/')
X64FLAGS = -Wlong-long -Wformat -Wpointer-arith
CFLAGS = -Dlinux  -Wall -Wno-deprecated
SSL = -DWITH_OPENSSL

ifeq ($(ARCH),x86_64)
	FLAGS = $(CFLAGS) $(X64FLAGS) $(SSL)
else
	FLAGS = $(CFLAGS) $(SSL)
endif

CFLAGS = -Dlinux  -Wall -Wno-deprecated $(SSL)
GSOAP_PATH = ./
GSOAP_CODE = ./
INC_PATH = ./Include
SRC_PATH = ./
INCLUDE = -I$(GSOAP_PATH)  -I$(INC_PATH)  -I$(GSOAP_CODE)
SRCS = $(GSOAP_CODE)/soapClient.cpp $(GSOAP_CODE)/soapC.cpp $(GSOAP_PATH)/stdsoap2.cpp $(GSOAP_PATH)/httpDigest.cpp $(GSOAP_PATH)/digcalc.cpp RemoteControlSample.cpp 
OBJS = $(SRCS:.cpp=.o) Utils.o 
LIBS = -lssl 
APPNAME = remoteControl
WSDL2H = $(GSOAP_PATH)/wsdl2h
SOAPCPP = $(GSOAP_PATH)/soapcpp2
all: clean $(APPNAME)

$(APPNAME): $(OBJS)   
	$(LIBTOOL) --mode=link $(CC) $(FLAGS) $(INCLUDE) -o $(APPNAME) $(OBJS) $(LIBS)       

Utils.o: $(SRC_PATH)/Utils.cpp 
	$(CC) $(CFLAGS) $(INCLUDE) -c $(SRC_PATH)/Utils.cpp -o Utils.o      

%.o: %.cpp
	$(CC) $(FLAGS) $(INCLUDE) -c $< -o $@ 

clean:
	rm -f $(OBJS) $(APPNAME) *~
	rm -rf .libs
	#dos2unix *.h
	#dos2unix *.cpp
	#dos2unix README
	#dos2unix Makefile
