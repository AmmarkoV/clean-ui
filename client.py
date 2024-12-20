import json
import time
import sys
import os
from gradio_client import Client, handle_file
#python3 -m pip install gradio-client


# Replace with the actual server URL if different
ip="127.0.0.1"
port="8080"

# Define the user prompt (caption)
user_prompt = "Thoroughly and carefully describe this image."

files = []
output_file = "output.json"

#Hyper parameters
temperature=0.6
top_k=50
top_p=0.9
max_tokens=100

startAt = 0

argumentStart = 1
if (len(sys.argv)>1):
       for i in range(0, len(sys.argv)):
           if (sys.argv[i]=="--ip"):
              ip = sys.argv[i+1]
              argumentStart = argumentStart+2
           if (sys.argv[i]=="--directory"):
              directory = sys.argv[i+1]
              argumentStart = argumentStart+2
              # Populate files with image (.jpg, .png) contents of directory
              if os.path.isdir(directory):
                directoryList = os.listdir(directory)
                directoryList.sort() 
                for file in directoryList:
                    if file.lower().endswith(('.jpg', '.png', '.jpeg','.txt')):
                        files.append(os.path.join(directory, file))
              else:
                print(f"Error: Directory '{directory}' does not exist.")
                sys.exit(1)
           elif (sys.argv[i]=="--start"):
              startAt = int(sys.argv[i+1])
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

results=dict()
results["prompt"] = user_prompt

for i in range(argumentStart, len(sys.argv)):
   files.append(sys.argv[i])

#Make sure the list is sorted
files.sort()

#Possibly start at specific index
for i in range(startAt,len(files)):

    #Grab next image path
    image_path = files[i]

    #Count start time
    start      = time.time()

    #Make query to VLLM
    try:
      imageFile = handle_file(image_path)
      if ('.txt' in image_path):
         imageFile = None
         this_user_prompt = user_prompt
         with open(image_path, 'r') as txt_file:
                this_user_prompt = txt_file.read().strip()
         
      else:
         imageFile = handle_file(image_path)
         this_user_prompt = user_prompt

      #Send the image file path and the prompt to the Gradio app for processing
      result = client.predict(
                              image=imageFile,   # Provide the file path directly
                              user_prompt=this_user_prompt,  # The user prompt
		                      temperature=temperature,
		                      top_k=top_k,
		                      top_p=top_p,
		                      max_tokens=max_tokens,
		                      history=[],
		                      api_name="/predict"
                             )     
    except Exception:
      print("Failed to complete job, please restart using --start ",i)
      output_file = "partial_until_%u%s" %(i,output_file) 
      break
    
    #Calculate elapsed time
    seconds    = time.time() - start
    remaining  = (len(files)-i) * seconds
    hz    = 1 / (seconds+0.0001)

    # Output the result
    question = result[0][0]
    response = result[0][1]
    
    #Printout on screen
    print("Processing ",1+i,"/",len(files)," | %0.2f Hz / remaining %0.2f minutes" % (hz, remaining/60))
    print("Image :",image_path,"\nResponse:", result[0][1])

    #Store each path as the key pointing to each description
    results[image_path]=response

print("\n\n\nStoring results in JSON file ",output_file)
with open(output_file, "w") as outfile: 
    json.dump(results, outfile, indent=4)
