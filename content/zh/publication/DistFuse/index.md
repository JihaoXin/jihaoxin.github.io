---
title: "Immediate Communication for Distributed AI Tasks"
authors:
  - Admin
  - Seongjong Bae
  - KyoungSoo Park
  - Marco Canini 
  - Changho Hwang
  - Peng Cheng

date: "2024-02-10T00:00:00Z"
doi: ""

# Schedule page publish date (NOT publication's date).
publishDate: "2024-02-10T00:00:00Z"

# Publication type.
# Legend: 0 = Uncategorized; 1 = Conference paper; 2 = Journal article;
# 3 = Preprint / Working Paper; 4 = Report; 5 = Book; 6 = Book section;
# 7 = Thesis; 8 = Patent
publication_types: ["1"]

# Publication name and optional abbreviated publication name.
publication: "SOSP Workshop on Hot Topics in System Infrastructure"
publication_short: "HotInfra'24"

abstract: Large AI models have necessitated efficient communication strategies across multi-GPU and multi-node infrastructures due to their increasing complexity. Current methods focusing on inter-operator overlaps fail when dependencies exist, leading to underutilized hardware. DistFuse addresses this by enabling fine-grained overlapping of computation and communication, triggering communication as soon as data is ready, and reducing latency. Initial experiments show up to 44.3% reduction in communication latency of Llama3-70B inference on a single node, demonstrating its potential to accelerate diverse AI workloads.

# Summary. An optional shortened abstract.
summary:

tags:
featured: false

# links:
# - name: ""
#   url: ""
url_pdf: 'https://hotinfra24.github.io/papers/hotinfra24-final2.pdf' 
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