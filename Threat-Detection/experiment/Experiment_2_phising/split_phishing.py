import os
import shutil

def split():
    txt_path = "/home/pndhpndh/CoT_Viettel/prompt_inj/cleaned/phishing_1000.txt"
    dest_dir = "/home/pndhpndh/CoT_Viettel/prompt_inj/dataset/phishing/Collection_extended"
    
    if not os.path.exists(txt_path):
        print(f"Error: {txt_path} does not exist.")
        return
        
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)
    
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        file_path = os.path.join(dest_dir, f"{idx}.txt")
        with open(file_path, "w", encoding="utf-8") as out:
            out.write(line)
            
    print(f"Successfully split {len(lines)} phishing emails into {dest_dir}")

if __name__ == "__main__":
    split()
