#!/bin/bash 

git clone https://github.com/deepseek-ai/DeepSeek-VL2
cd DeepSeek-VL2
python3 -m venv venv
source venv/bin/activate

python3 -m pip install -e .
python3 -m pip install -e .[gradio]

python3 -m pip install joblib wheel
python3 -m pip install flash-attn --no-build-isolation
python3 -m pip install xformers
python3 -m pip install --upgrade gradio

CUDA_VISIBLE_DEVICES=2 python3 web_demo.py --model_name "deepseek-ai/deepseek-vl2-tiny"  --port 37914


exit 0

