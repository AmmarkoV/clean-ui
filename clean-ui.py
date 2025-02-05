import gradio as gr
import torch
import os
import sys
from PIL import Image
from transformers import MllamaForConditionalGeneration, AutoModelForCausalLM, AutoProcessor, GenerationConfig

# Set memory management for PyTorch
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'  # or adjust size as needed


port="8080"
server_name="127.0.0.1"

model_choice="0"
if (len(sys.argv)>1):
       for i in range(0, len(sys.argv)):
           if (sys.argv[i]=="--deepseek"):
              model_choice="4"
           if (sys.argv[i]=="--llama"):
              model_choice="1"
           if (sys.argv[i]=="--llama90"):
              model_choice="2"
           if (sys.argv[i]=="--molmo"):
              model_choice="3"
           if (sys.argv[i]=="--bind_all") or (sys.argv[i]=="--bindall"):
              server_name="0.0.0.0"
           if (sys.argv[i]=="--bind"):
              server_name = sys.argv[i+1]
              port        = sys.argv[i+2]


if (model_choice=="0"):
    # Model selection menu in terminal
   print("Select a model to load:")
   print("1. Llama-3.2-11B-Vision-Instruct-bnb-4bit")
   print("2. Llama-3.2-90B-Vision-Instruct")
   print("3. Molmo-7B-D-bnb-4bit")
   print("4. Deep Seek VL2")
   model_choice = input("Enter the number of the model you want to use: ")

if model_choice == "1":
    model_id = "unsloth/Llama-3.2-11B-Vision-Instruct-bnb-4bit"
    model = MllamaForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    processor = AutoProcessor.from_pretrained(model_id)
elif model_choice == "2":
    #model_id = "meta-llama/Llama-3.2-90B-Vision-Instruct"
    model_id = "neuralmagic/Llama-3.2-90B-Vision-Instruct-FP8-dynamic"
    model = MllamaForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    processor = AutoProcessor.from_pretrained(model_id)
elif model_choice == "3":
    model_id = "cyan2k/molmo-7B-D-bnb-4bit"
    arguments = {"device_map": "auto", "torch_dtype": "auto", "trust_remote_code": True}
    model = AutoModelForCausalLM.from_pretrained(model_id, **arguments)
    processor = AutoProcessor.from_pretrained(model_id, **arguments)
elif model_choice == "4":
    model_id = "deepseek-ai/deepseek-vl2-small"
    model:DeepseekVLV2ForCausalLM = AutoModelForCausalLM.from_pretrained(model_id, auto_map=True, trust_remote_code=True)
    model = model.to(torch.bfloat16).cuda().eval()
    from deepseek_vl.models import DeepseekVLV2Processor, DeepseekVLV2ForCausalLM
    processor: DeepseekVLV2Processor = DeepseekVLV2Processor.from_pretrained(model_id)
else:
    raise ValueError("Invalid model choice. Please enter 1 or 2.")

# Visual theme
visual_theme = gr.themes.Default()  # Default, Soft or Monochrome

# Constants
MAX_OUTPUT_TOKENS = 2048
MAX_IMAGE_SIZE = (1120, 1120)

# Function to process the image and generate a description
def describe_image(image, user_prompt, temperature, top_k, top_p, max_tokens, history):
    # Resize image if necessary
    if image is not None:
       image = image.resize(MAX_IMAGE_SIZE)

    # Initialize cleaned_output variable
    cleaned_output = ""

    # Prepare prompt with user input based on selected model
    if model_choice == "1" or model_choice == "2":  # Llama Model
        if image is not None:
           prompt = f"<|image|><|begin_of_text|>{user_prompt} Answer:"
        else:
           prompt = f"<|begin_of_text|>{user_prompt} Answer:"
        # Preprocess the image and prompt
        inputs = processor(image, prompt, return_tensors="pt").to(model.device)

        # Generate output with model
        output = model.generate(
            **inputs,
            max_new_tokens=min(max_tokens, MAX_OUTPUT_TOKENS),
            temperature=temperature,
            top_k=top_k,
            top_p=top_p
        )

        # Decode the raw output
        raw_output = processor.decode(output[0])
        
        # Clean up the output to remove system tokens
        
        if image is not None:
          cleaned_output = raw_output.replace("<|image|><|begin_of_text|>", "").strip().replace(" Answer:", "")
        else:
          cleaned_output = raw_output.replace("<|begin_of_text|>", "").strip().replace(" Answer:", "")        
    elif model_choice == "3":  # Molmo Model
        # Prepare inputs for Molmo model
        inputs = processor.process(images=[image], text=user_prompt)
        inputs = {k: v.to(model.device).unsqueeze(0) for k, v in inputs.items()}
        
        # Generate output with model, applying the parameters for temperature, top_k, top_p, and max_tokens
        output = model.generate_from_batch(
            inputs,
            GenerationConfig(
                max_new_tokens=min(max_tokens, MAX_OUTPUT_TOKENS),
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                stop_strings="<|endoftext|>",
                do_sample=True
            ),
            tokenizer=processor.tokenizer,
        )

        # Extract generated tokens and decode them to text
        generated_tokens = output[0, inputs["input_ids"].size(1):]
        cleaned_output = processor.tokenizer.decode(generated_tokens, skip_special_tokens=True)
    elif model_choice == "4":  # Deep Seek
        conversation = [
        {
        "role": "<|User|>",
        "content": "<image>\n %s" % user_prompt,
        "images": [image],
        },
        {"role": "<|Assistant|>", "content": ""},
        ]
        from deepseek_vl.utils.io import load_pil_images
        pil_images = load_pil_images(conversation)
        prepare_inputs = vl_chat_processor(
                                           conversations=conversation,
                                           images=pil_images,
                                           force_batchify=True,
                                           system_prompt=""
                                          ).to(vl_gpt.device)

        # run image encoder to get the image embeddings
        inputs_embeds = vl_gpt.prepare_inputs_embeds(**prepare_inputs)

        # run the model to get the response
        outputs = vl_gpt.language_model.generate(
                                                 inputs_embeds=inputs_embeds,
                                                 attention_mask=prepare_inputs.attention_mask,
                                                 pad_token_id=tokenizer.eos_token_id,
                                                 bos_token_id=tokenizer.bos_token_id,
                                                 eos_token_id=tokenizer.eos_token_id,
                                                 max_new_tokens=512,
                                                 do_sample=False,
                                                 use_cache=True
                                                )

        cleaned_output = tokenizer.decode(outputs[0].cpu().tolist(), skip_special_tokens=True)
        print(f"{prepare_inputs['sft_format'][0]}", cleaned_output)






    # Ensure the prompt is not repeated in the output
    if cleaned_output.startswith(user_prompt):
        cleaned_output = cleaned_output[len(user_prompt):].strip()
        
    # Append the new conversation to the history
    history.append((user_prompt, cleaned_output))

    return history

# Function to clear the chat history
def clear_chat():
    return []

# Gradio Interface
def gradio_interface():
    with gr.Blocks(visual_theme) as demo:
        gr.HTML(
        """
    <h1 style='text-align: center'>
    Clean-UI
    </h1>
    """)
        with gr.Row():
            # Left column with image and parameter inputs
            with gr.Column(scale=1):
                image_input = gr.Image(
                    label="Image", 
                    type="pil", 
                    image_mode="RGB", 
                    height=512,  # Set the height
                    width=512   # Set the width
                )

                # Parameter sliders
                temperature = gr.Slider(
                    label="Temperature", minimum=0.1, maximum=2.0, value=0.6, step=0.1, interactive=True)
                top_k = gr.Slider(
                    label="Top-k", minimum=1, maximum=100, value=50, step=1, interactive=True)
                top_p = gr.Slider(
                    label="Top-p", minimum=0.1, maximum=1.0, value=0.9, step=0.1, interactive=True)
                max_tokens = gr.Slider(
                    label="Max Tokens", minimum=50, maximum=MAX_OUTPUT_TOKENS, value=100, step=50, interactive=True)

            # Right column with the chat interface
            with gr.Column(scale=2):
                chat_history = gr.Chatbot(label="Chat", height=512)

                # User input box for prompt
                user_prompt = gr.Textbox(
                    show_label=False,
                    container=False,
                    placeholder="Enter your prompt", 
                    lines=2
                )

                # Generate and Clear buttons
                with gr.Row():
                    generate_button = gr.Button("Generate")
                    clear_button = gr.Button("Clear")

                # Define the action for the generate button
                generate_button.click(
                    fn=describe_image, 
                    inputs=[image_input, user_prompt, temperature, top_k, top_p, max_tokens, chat_history],
                    outputs=[chat_history],
                    api_name="predict"
                )

                # Define the action for the clear button
                clear_button.click(
                    fn=clear_chat,
                    inputs=[],
                    outputs=[chat_history]
                )

    return demo

# Launch the interface
demo = gradio_interface()
demo.launch(server_name=server_name, server_port=int(port))
