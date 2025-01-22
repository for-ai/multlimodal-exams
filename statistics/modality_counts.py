import pandas as pd
import json
import os
import argparse
from collections import defaultdict
from huggingface_hub import HfApi, HfFolder, Repository
from huggingface_hub import hf_hub_download
from rich.console import Console
from rich.table import Table


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
  table.add_column("Text", justify="right")
  table.add_column("Multimodal", justify="right")
  table.add_column("Total", justify="right")
  grand_total = grand_text = grand_multimodal = 0

  for link in hf_links:
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
    json_files = [file for file in repo_files if file.endswith(".json")]
    print(json_files)
    save_dir = os.path.join(local_dir, repo.replace("/", "__"))
    os.makedirs(save_dir, exist_ok=True)
    for json_file in json_files:
      print(repo)
      hf_hub_download(repo_id=repo, filename=json_file, repo_type="dataset", 
                      local_dir=save_dir)
      json_path = f"{save_dir}/{json_file}"
      
      try:
        with open(json_path, "r", encoding="utf-8") as f:
          try:
            json_data = json.load(f)
          except:        
            json_data = [json.loads(line) for line in f]
      except:
        print(f"Error reading {json_path}")
        continue
      
      counts = defaultdict(int)
      for data in json_data:
        is_mutlimodal = False
        for option in data['options']:
          if ".png" in option:
            is_mutlimodal = True
            break
        
        if data['image_png']:
          is_mutlimodal = True
        
        if is_mutlimodal:
          counts['multimodal'] += 1
        else:
          counts['text'] += 1
      
      counts['total'] = len(json_data)
      print(dict(counts))
      print('-'*80)

      grand_total += counts['total']
      grand_multimodal += counts['multimodal']
      grand_text += counts['text']
      
      table.add_row(repo, json_file, str(counts['text']), 
                    str(counts['multimodal']), str(counts['total']))
    # break
  
  # Add a horizontal line
  table.add_row("-" * 80, "-" * 80, "-" * 80, "-" * 80, "-" * 80)
  table.add_row("Total", "", str(grand_text), str(grand_multimodal), str(grand_total))
  console.print(table)
    
# Take local_dir as input from argparse
if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--local_dir", type=str, default="./hub_data")
  args = parser.parse_args()
  local_dir = args.local_dir
  main(local_dir)
