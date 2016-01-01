#!/bin/bash

echo -e "\e[1;31mInstalling packages...\e[0m"
apt-get install build-essential libtool autotools-dev automake checkinstall check git yasm python-pip python-opencv libportaudio-dev libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev python-dev python-pyaudio

echo -e "\e[1;31mInstalling packages needed for libtoxav\e[0m"
apt-get install libopus-dev libvpx-dev pkg-config

echo -e "\e[1;31mCloning libsodium tarball...\e[0m"
wget https://download.libsodium.org/libsodium/releases/libsodium-1.0.8.tar.gz
tar -xf libsodium-1.0.8.tar.gz
rm libsodium-1.0.8.tar.gz
pushd libsodium-1.0.8
    echo -e "\e[1;31mInstalling libsodium...\e[0m"
    ./configure
    make && make check
    make install
popd

echo -e "\e[1;31mCloning toxcore repo...\e[0m"
git clone git://github.com/irungentoo/toxcore.git
pushd toxcore
    echo -e "\e[1;31mBuilding and installing toxcore...\e[0m"
    autoreconf -i
    ./configure
    make
    make install
popd

echo -e "Running ldconfig"
echo '/usr/local/lib/' | sudo tee -a /etc/ld.so.conf.d/locallib.conf
ldconfig
