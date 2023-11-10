# CS6120-L13-synthesis
CS6120 Lesson 13 Program Synthesis

## What this does

- Search for low operation cost methods for GCD choosing between two algorithm loop bodies usin Z3 SMT solver

## Why

- To explore program synthesis and satisfiability analyses

## Inspired by

- [CS6120 L13](https://www.cs.cornell.edu/courses/cs6120/2023fa/lesson/13/) [Program Synthesis](https://www.cs.cornell.edu/~asampson/blog/minisynth.html) [Tutorial](https://github.com/sampsyo/minisynth)

## Setup

- install a [Docker](https://docs.docker.com/engine/install/) runtime like [Colima](https://github.com/abiosoft/colima) on Mac

- `docker pull ghcr.io/z3prover/z3:ubuntu-20.04-bare-z3-sha-14312ef`

- [containers cheat sheet](https://github.com/wsargent/docker-cheat-sheet#containers)
    - `docker images`
    - `docker run -it --platform linux/amd64 --entrypoint=bash ghcr.io/z3prover/z3:ubuntu-20.04-bare-z3-sha-14312ef`

- tutorial
    - `cd /`
    - `git clone https://github.com/sampsyo/minisynth.git`

- software
```
apt update && apt upgrade -y && apt install -y git vim wget
apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev
pwd # z3-source
# Python 3.12 from source
cd /tmp
wget https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz
tar -xzvf Python-3.12.0.tgz
cd Python-3.12.0/
./configure --enable-optimizations || ./configure --enable-optimizations
echo $?  # want 0
make -j 2 || make || make -j 2 || make -j 2
echo $?  # want 0

make altinstall
python3.12 -V
# Python 3.12.0

# ln -s /usr/local/bin/python3.12 /usr/local/bin/python
# ls -al /usr/local/bin/python
# python -VV
# Python 3.12.0 ...


# Run Z3 for GCD algorithm comparison by operation cost over a range of inputs
cd /
git clone https://github.com/rcplane/CS6120-L13-synthesis.git
cd CS6120-L13-synthesis
python gcd.py
```







