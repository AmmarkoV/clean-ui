import sys
from gradio_client import Client, handle_file
#python3 -m pip install gradio_client


# Replace with the actual server URL if different
ip="139.91.90.47"
port="8080"

# Define the user prompt (caption)
user_prompt = "Thoroughly and carefully describe this image."

output_file = "output.csv"

#Hyper parameters
temperature=0.6
top_k=50
top_p=0.9
max_tokens=100

argumentStart = 0
if (len(sys.argv)>1):
       for i in range(0, len(sys.argv)):
           if (sys.argv[i]=="--ip"):
              ip = sys.argv[i+1]
              argumentStart = argumentStart+2
           elif (sys.argv[i]=="--port"):
              port = sys.argv[i+1]
              argumentStart = argumentStart+2
           elif (sys.argv[i]=="--prompt"):
              user_prompt=sys.argv[i+1]
              argumentStart = argumentStart+2
           elif (sys.argv[i]=="--temperature"):
              temperature = float(sys.argv[i+1])
              argumentStart = argumentStart+2
           elif (sys.argv[i]=="--top_k"):
              top_k = int(sys.argv[i+1])
              argumentStart = argumentStart+2
           elif (sys.argv[i]=="--top_p"):
              top_p = float(sys.argv[i+1])
              argumentStart = argumentStart+2
           elif (sys.argv[i]=="--max_tokens"):
              max_tokens = int(sys.argv[i+1])
              argumentStart = argumentStart+2
           elif ((sys.argv[i]=="--output") or (sys.argv[i]=="-o")):
              output_file = sys.argv[i+1]
              argumentStart = argumentStart+2

# Initialize the Gradio client with the server URL
client = Client("http://%s:%s"%(ip,port))  
#client.view_api() 

with open(output_file, "w") as file:
 for i in range(argumentStart, len(sys.argv)):
    file.write("input,output\n") 
    # Path to the image
    image_path = sys.argv[i]
    file.write(image_path) 
    file.write(",") 
    
    # Send the image file path and the prompt to the Gradio app for processing
    result = client.predict(
                            image=handle_file(image_path),   # Provide the file path directly
                            user_prompt=user_prompt,  # The user prompt
		                    temperature=temperature,
		                    top_k=top_k,
		                    top_p=top_p,
		                    max_tokens=max_tokens,
		                    history=[],
		                    api_name="/predict"
                           )

    # Output the result
    question = result[0][0]
    response = result[0][1]
    
    #Printout on screen
    print("Processing ",i-argumentStart,"/",len(sys.argv))
    print("Image :",image_path,"\nResponse:", result[0][1])

    file.write("\"") 
    file.write(response) 
    file.write("\"\n") 
