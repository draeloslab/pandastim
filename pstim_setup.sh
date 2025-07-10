#!/bin/bash

cd $HOME/Desktop/Code/pandastim/ || exit

source ~/miniforge3/etc/profile.d/conda.sh  
conda activate pstim

export PYTHONPATH=$HOME/Desktop/Code/:$PYTHONPATH
