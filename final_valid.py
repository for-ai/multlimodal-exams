import pandas as pd
import json
import os
import argparse
from collections import defaultdict
from huggingface_hub import HfApi, HfFolder, Repository
from huggingface_hub import hf_hub_download
from huggingface_hub import snapshot_download

from rich.console import Console
from rich.table import Table
import shutil


def main(local_dir):
  api = HfApi()

  sheet = "Completed_and_Validated_Exams"
  gsheet_id = "1f4nkmFyTaYu0-iBeRQ1D-KTD3JoyC-FI7V9G6hTdn5o"
  data_url = f"https://docs.google.com/spreadsheets/d/{gsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"

  df = pd.read_csv(data_url)
  HF_column = 'HF Dataset Link'
  hf_links = df[HF_column].dropna().tolist()
  print(hf_links)

  hf_links = [link.replace("tree/main", "") for link in hf_links]
  print(hf_links)
  
  console = Console()
  table = Table(show_header=True, header_style="bold magenta")
  table.add_column("Repo", justify="left")
  table.add_column("JSON", justify="right")
  table.add_column("Multimodal", justify="right")
  table.add_column("Text", justify="right")
  table.add_column("Total", justify="right")
  grand_total = grand_text = grand_multimodal = 0
  
  visited = defaultdict(bool)
  for idx, link in enumerate(hf_links):
    break
    if visited[link]:
      continue
    visited[link] = True
    link = link.strip()
    if not link.startswith("https://"):
      continue
    
    if link.endswith("/"):
      link = link[:-1]
    link = link.strip()
    repo_user = link.split("/")[-2]
    repo_id = link.split("/")[-1]
    repo = f"{repo_user}/{repo_id}"
    repo_files = api.list_repo_files(repo, repo_type="dataset")
    # Download full repo from hub
    
    save_dir = os.path.join(local_dir, f"{idx:03d}__"+ repo.replace("/", "__"))
    # old_save_dir = os.path.join(local_dir, repo.replace("/", "__"))
    # shutil.move(old_save_dir, save_dir)
    try:
      snapshot_download(repo_id=repo, repo_type="dataset", 
                      local_dir=save_dir, max_workers=8)
    except:
      # Access issue
      print( f"Access issue with {repo}")
  
  # For all json files in the local_dir open and save as indent=2, ensure ascii=False
  
  for root, dirs, files in os.walk(local_dir):
    # Skip ".cache" directories
    
    for file in files:
      if file.endswith(".json"):
        # import ipdb; ipdb.set_trace()
        valid_file = os.path.join(root, "valid__" + file)
        if file.startswith("valid__"):
          continue
        
        with open(os.path.join(root, file), "r", encoding="utf-8") as f:
          data = json.load(f)
          # Get category_en, category_original_lang and print set
          cats_en = set()
          cats_original = set()
          image_png = set()
          image_information = set()
          
          for item in data:
            cats_en.add(item["category_en"])
            cats_original.add(item["category_original_lang"])
            image_information.add(item["image_information"])
            image_png.add(item["image_type"])
          print(os.path.join(root, file))
          print(f"Category_en: {cats_en}")
          print(f"Category_original_lang: {cats_original}")
          print(f"Image information: {image_information}")
          print(f"Image type: {image_png}")
          print("-"*80)
        
        if os.path.exists(valid_file):
          continue
        
        with open(os.path.join(root, "valid__" + file), "w", encoding="utf-8") as f:
          json.dump(data, f, indent=2, ensure_ascii=False)
  
  # find . -type f -name "*.zip" -exec sh -c 'unzip -d "${1%.*}" "$1"' _ {} \;
  # find . -type f -name "valid__*.json" -delete
    
# Take local_dir as input from argparse
if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--local_dir", type=str, default="./a_final_validation")
  args = parser.parse_args()
  local_dir = args.local_dir
  main(local_dir)
