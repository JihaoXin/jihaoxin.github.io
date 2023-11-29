---
title: "Global QSGD: Practical Floatless Quantization for Distributed Learning with Theoretical Guarantees"
authors:
  - Admin
  - Marco Canini
  - Peter Richtárik
  - Samuel Horváth

date: "2023-08-08T00:00:00Z"
doi: "10.48550/arXiv.2305.18627"
 
# Schedule page publish date (NOT publication's date).
publishDate: "2022-11-08T00:00:00Z"

# Publication type.
# Legend: 0 = Uncategorized; 1 = Conference paper; 2 = Journal article;
# 3 = Preprint / Working Paper; 4 = Report; 5 = Book; 6 = Book section;
# 7 = Thesis; 8 = Patent
publication_types: ["3"]

# Publication name and optional abbreviated publication name.
publication: "*EuroSys 2023 Poster*"
publication_short: "Preprint (Poster accepted at Eurosys'23)"

abstract: The increase of deep learning models and dataset sizes make training time-consuming, while heavy communication, primarily due to gradients synchronization as a key bottleneck. Sapio et al. [7] show that communication can take up to 90% of a training iteration. A popular remedy is to reduce the size of communication data between nodes by applying gradient compression methods [1, 3, 6, 8, 9, 11]. Unfortunately, a majority of the proposed compressors are not natively compatible with the AllReduce collective communication primitive because of the change in data format and the need for custom reduction operations. To the best of our knowledge, the only compressors compatible with AllReduce are PowerSGD [10] and IntSGD [5, 7]. However, practical implementations of these methods are heuristic-based and do not come with rigorous theoretical guarantees. Concurrently, C-Coll [4] proposes error-bounded lossy compression with MPI collectives. We address this question can we provide theoretical guarantees for gradient compression while retaining AllReduce compatibility for an efficient implementation?

# Summary. An optional shortened abstract.
summary:

tags:
featured: false

# links:
# - name: ""
#   url: ""
url_pdf: 'https://arxiv.org/pdf/2305.18627.pdf' 
url_code: ''
url_dataset: ''
url_poster: 'https://2023.eurosys.org/accepted-posters.html#accepted-posters'
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