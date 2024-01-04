import torch
from diffusers import AutoPipelineForImage2Image
from transformers import Pipeline

device: str = "cuda" if torch.cuda.is_available() else "cpu"
dtype: torch.dtype = (  # pytorch doesn't support float16 on CPU
    torch.float16 if device == "cuda" else torch.float32
)
# variant: str =  if device == "cuda" else "fp32"
pipe: Pipeline = AutoPipelineForImage2Image.from_pretrained(
    "stabilityai/sdxl-turbo", torch_dtype=dtype, variant="fp16"
)
