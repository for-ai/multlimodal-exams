## Usage

```bash
python vlm_metadata.py \
	--api_base_url https://openrouter.ai/api/v1 \
	--api_key $API_KEY \
	--model meta-llama/llama-3.2-90b-vision-instruct:free \
	--input_json dataset.json

# Output saved at dataset_with_metadata.json
```



The API Key can be derived from [https://openrouter.ai/](https://openrouter.ai/) which has two free vision models with Rate Limits: 
- `meta-llama/llama-3.2-11b-vision-instruct:free`
- `meta-llama/llama-3.2-90b-vision-instruct:free`

It is advisable to use the bigger model and verify manually after inference.
