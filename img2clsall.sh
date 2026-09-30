#!/bin/bash
set -e
for i in */*/*/*/;do
	pushd $i
	[ -a F ]||{ img2cls.py rename '' 3 *.webp;xdg-open .;read -p'rename light->F dark->PROCESS and hit enter';}
	pushd DURING
	[ -a FLOW ]||{ img2cls.py symlink FLOW/ 20 *.webp;xdg-open FLOW;read -p'rename no flow->*n and hit enter';}
	popd
	pushd F
	[ -a FLOW ]||{ img2cls.py symlink FLOW/ 20 *.webp;xdg-open FLOW;read -p'rename flow->*n and hit enter';}
	[ -a SB ]||{ img2cls.py symlink SB/ 100 *.webp;xdg-open SB;read -p'rename wired sb->*n and hit enter';}
	[ -a NOZLE ]||{ img2cls.py symlink NOZLE/ 20 *.webp;xdg-open NOZLE;read -p'rename wired nozle->*n and hit enter';}
	[ -a DIRT ]||{ img2cls.py symlink DIRT/ 20 *.webp;xdg-open DIRT;read -p'rename dirt->*n and hit enter';}
	popd
	popd
done
