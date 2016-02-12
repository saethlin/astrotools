#!/bin/bash
#This script will install Python with all the basics for astronomy work
#It expects two command line arguments, the python version and
#the directory for the install. At UF, I suggest /scratch/python to keep
#your /scratch tidy.

#Need to do something about permissions

#Check for command line arguments
if [ "$#" -ne 2 ]; then
    echo "Illegal number of parameters."
    echo "Example: bash setup_python.sh 3.5.0 /scratch/python"
    exit
fi


#mkdir $2

# First we need to get openssl
#mkdir $2/openssl
#cd $2/openssl
#wget http://www.openssl.org/source/openssl-0.9.8g.tar.gz
#tar xvfz openssl-0.9.8g.tar.gz
#cd openssl-0.9.8g
#Using asm causes some strange errors
#./config no-asm --prefix=$2/openssl --openssldir=$2/openssl
#make
#make install

#Need lssl?
#Need lcrypto?

#above suggested by installing libssl-dev

# Get the specified version of Python
cd $2
wget https://www.python.org/ftp/python/$1/Python-$1.tgz
tar -zxvf Python-$1.tgz


#Manually specify openssl installation in Python setup

cd $2/Python-$1/Modules

#_socket socketmodule.c
sed -i "s|\#_socket socketmodule.c|_socket socketmodule.c|" Setup.dist
sed -i "s|\#SSL=/usr/local/ssl|SSL=$2/openssl/openssl-0.9.8g|" Setup.dist
#sed -i "s|\#_ssl _ssl.c|_ssl \_ssl.c -DUSE_SSL -I\$(SSL)/include -I\$(SSL)/include/openssl -L\$(SSL)/lib -lssl -lcrypto|" Setup.dist


#Install Python
cd $2/Python-$1
./configure --prefix=$2
make
make install

exit

#Need zlib installed


#Need libpng to support matplotlib
cd $2
wget http://prdownloads.sourceforge.net/libpng/libpng-1.6.18.tar.xz
tar xvfJ libpng-1.6.18.tar.xz
cd libpng-1.6.18
./configure --prefix=$2
make
make install


#Install the basic packages
for package in numpy scipy matplotlib astropy pillow
do
    $2/Python-$1/Lib/pip install $package
done
