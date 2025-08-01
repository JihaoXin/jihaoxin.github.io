---
title: "Quantize Once, Train Fast: Allreduce-Compatible Compression with Provable Guarantees"
authors:
  - Admin
  - Marco Canini
  - Peter Richtárik
  - Samuel Horváth

date: "2025-10-25T00:00:00Z"

# Schedule page publish date (NOT publication's date).
publishDate: "2022-11-08T00:00:00Z"

# Publication type.
# Legend: 0 = Uncategorized; 1 = Conference paper; 2 = Journal article;
# 3 = Preprint / Working Paper; 4 = Report; 5 = Book; 6 = Book section;
# 7 = Thesis; 8 = Patent
publication_types: ["1"]

# Publication name and optional abbreviated publication name.
publication: "*ECAI*"
publication_short: "ECAI (CCF B)"

abstract: Distributed training enables large-scale deep learning, but suffers from high communication overhead, especially as models and datasets grow. Gradient compression, particularly quantization, is a promising approach to mitigate this bottleneck. However, existing quantization schemes are often incompatible with Allreduce, the dominant communication primitive in distributed deep learning, and many prior solutions rely on heuristics without theoretical guarantees. We introduce Global-QSGD, an Allreduce-compatible gradient quantization method that leverages global norm scaling to reduce communication overhead while preserving accuracy. Global-QSGD is backed by rigorous theoretical analysis, extending standard unbiased compressor frameworks to establish formal convergence guarantees. Additionally, we develop a performance model to evaluate its impact across different hardware configurations. Extensive experiments on NVLink, PCIe, and large-scale cloud environments show that Global-QSGD accelerates distributed training by up to 3.51% over baseline quantization methods, making it a practical and efficient solution for large-scale deep learning workloads.

# Summary. An optional shortened abstract.
summary:

tags:
featured: false

# links:
# - name: ""
#   url: ""
url_pdf: 'https://arxiv.org/pdf/2305.18627' 
url_code: ''
url_dataset: ''
url_poster: ''
url_project: ''
url_slides: ''
url_source: ''
url_video: ''

# Featured image
# To use, add an image named `featured.jpg/png` to your page's folder. 
image:
  caption: 
  focal_point: 
  preview_only: false

# Associated Projects (optional).
#   Associate this publication with one or more of your projects.
#   Simply enter your project's folder or file name without extension.
#   E.g. `internal-project` references `content/project/internal-project/index.md`.
#   Otherwise, set `projects: []`.
projects: []

# Slides (optional).
#   Associate this publication with Markdown slides.
#   Simply enter your slide deck's filename without extension.
#   E.g. `slides: "example"` references `content/slides/example/index.md`.
#   Otherwise, set `slides: ""`.
slides: ""
---