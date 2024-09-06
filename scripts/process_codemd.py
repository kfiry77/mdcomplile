import os
import sys
import zlib
import requests
import base64

PLANTUML_SERVER = "http://www.plantuml.com/plantuml"

# Custom Base64 encoding for PlantUML
def plantuml_encode(text):
    utf8_encoded = text.encode('utf-8')
    compressed = zlib.compress(utf8_encoded, 9)[2:-4]
    base64_encoded = base64.b64encode(compressed).decode('utf-8')
    plantuml_encoded = base64_encoded.translate(str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/', '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'))
    return plantuml_encoded

def process_codemd(source_file, output_dir):
    destination_file = os.path.basename(source_file).replace('.src.md', '.md')
    print(f"Processing {source_file}, output_dir {output_dir} saving to {destination_file}")
    counter = 1
    os.makedirs(output_dir, exist_ok=True)

    with open(source_file, "r") as file:
        lines = file.readlines()

    temp_lines = []
    inside_code_block = False
    code_block = ""
    is_special_diagram = False

    # Keywords that indicate special diagrams where @startuml/@enduml should not be added
    special_diagrams = ["@startditaa", "@startgantt", "@startmindmap", "@startjson", "@startyaml"]

    for line in lines:
        if inside_code_block:
            if line.strip() == "```":
                filename = f"{os.path.basename(source_file).replace('.src.md', '')}_diagram_{counter}.svg"
                output_file_path = os.path.join(output_dir, filename)
                print('output_file_path:', output_file_path)

                # Wrap with @startuml/@enduml if not a special diagram
                if not is_special_diagram and "@startuml" not in code_block:
                    code_block = f"@startuml\n{code_block.strip()}\n@enduml\n"

                # Encode the PlantUML code
                encoded_diagram = plantuml_encode(code_block)
                
                response = requests.get(f"{PLANTUML_SERVER}/svg/{encoded_diagram}")

                if response.status_code == 200:
                    with open(output_file_path, "wb") as svg_file:
                        svg_file.write(response.content)
                else:
                    print(f"Error: Unable to generate diagram for {filename}")

                temp_lines.append(f"![Diagram {counter}](./{output_dir}/{filename})")
                temp_lines.append(f'\n<details>\n <summary>Diagram {counter} plantuml</summary>\n\n')
                temp_lines.append(f'```plantuml\n')
                temp_lines.append(f"{code_block}")
                temp_lines.append(f'```\n</details>\n')

                counter += 1
                inside_code_block = False
                is_special_diagram = False
            else:
                code_block += line                
            continue

        if line.strip() == "```plantuml":
            inside_code_block = True
            code_block = ""
        elif any(diagram in line for diagram in special_diagrams):
            inside_code_block = True
            is_special_diagram = True
            code_block = line  # Start the block with the special diagram keyword
        else:
            temp_lines.append(line)

    # Write the modified content to the destination .md file    
    with open(destination_file, "w") as md_file:
        md_file.writelines(temp_lines)

    print(f"Finished processing {source_file}, saved to {destination_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python process_codemd.py <source_file.src.md> <destination_folder>")
        sys.exit(1)
    
    process_codemd(sys.argv[1], sys.argv[2])
