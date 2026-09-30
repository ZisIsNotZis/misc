#!/bin/sh
dpkg -l|grep -v ^ii
sudo apt update
sudo apt-mark auto `apt-mark showmanual`
sudo apt full-upgrade --autoremove --purge \
bleachbit \
ccache \
cmake \
code \
codemeter-lite \
cryptsetup-initramfs \
cuda-keyring \
cuda-toolkit \
cudnn \
docker-ce \
ffmpeg \
gnome-screenshot \
gparted \
ifuse \
intel-basekit \
intel-mkl-full \
intel-oneapi-mkl \
libmfx-gen1 \
libstdc++-14-dev \
libva-glx2 \
libze-intel-gpu1 \
linux-generic-hwe-24.04-edge \
linux-headers-generic-hwe-24.04-edge \
maven \
mpv \
nmap \
nvidia-driver-595 \
nvidia-prime \
openjdk-17-jdk-headless \
powertop \
rdfind \
rename \
shadowsocks-libev \
sublime-text \
trae-cn \
ubuntu-desktop-minimal \
ubuntu-minimal \
ubuntu-standard \
winehq-stable \
xdotool \
ydotool \
yq \
\
freerdp3-wayland \
git-lfs \
gnupg-pkcs11-scd \
intune-portal \
inxi \
krb5-pkinit \
libpam-passwdqc \
libreoffice \
libtpm2-pkcs11-1 \
libtpm2-pkcs11-tools \
mdatp \
microsoft-edge-stable \
moreutils \
onedrive \
p7zip-full \
pcsc-tools \
puppet-agent \
python3-pydbus \
siemens-certificates \
tpm2-openssl \
zscaler-client \
\
autokey-gtk \
freeglut3-dev \
libfreetype-dev \
libgsettings-qt1 \
libirrlicht-dev \
libjpeg-dev \
liblzma-dev \
liblua5.3-dev \
liblua5.4-dev \
libminiaudio-dev \
libmono-system-data4.0-cil \
libmono-system-runtime-serialization4.0-cil \
libsqlite3-dev \
qml-module-qtquick2 \
sogoupinyin \
sqlite3 \
wechat \
xclip
