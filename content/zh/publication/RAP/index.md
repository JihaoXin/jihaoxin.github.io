---
title: "KV-Cache Compression via RoPE-Aligned Pruning"
authors:
  - Admin
  - Tian Lyu
  - David Keyes
  - Hatem Ltaief
  - Marco Canini

date: "2026-02-04T00:00:00Z"

# Schedule page publish date (NOT publication's date).
publishDate: "2026-02-04T00:00:00Z"

# Publication type.
# Legend: 0 = Uncategorized; 1 = Conference paper; 2 = Journal article;
# 3 = Preprint / Working Paper; 4 = Report; 5 = Book; 6 = Book section;
# 7 = Thesis; 8 = Patent
publication_types: ["3"]

# Publication name and optional abbreviated publication name.
publication: "arXiv preprint"
publication_short: "arXiv"

abstract: Long-context inference in large language models is bottlenecked by KV-Cache memory consumption. RAP (RoPE-Aligned Pruning) prunes RoPE-aligned column pairs to preserve rotation structure, enables B absorption, and eliminates reconstruction overhead. RAP achieves 20-30% joint reduction of KV-Cache, attention parameters, and FLOPs on LLaMA-3-8B and Mistral-7B, with attention latency reduced to 83% for prefill and 77% for decode.

# Summary. An optional shortened abstract.
summary:

tags:
featured: false

url_pdf: 'https://arxiv.org/pdf/2602.02599'
url_code: ''
url_dataset: ''
url_poster: ''
url_project: ''
url_slides: ''
url_source: ''
url_video: ''

image:
  caption: 
  focal_point: 
  preview_only: false

projects: []
slides: ""
---
