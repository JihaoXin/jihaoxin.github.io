---
title: "Assassyn: A Unified Abstraction for Architectural Simulation and Implementation"
authors:
  - Jian Weng
  - Boyang Han
  - Derui Gao
  - Ruijie Gao
  - Wanning Zhang
  - Ceyu Xu
  - Admin
  - Yangzhixin Luo
  - Lisa Wu Wills
  - Marco Canini

date: "2025-06-21T00:00:00Z"
doi: ""

# Schedule page publish date (NOT publication's date).
publishDate: "2024-02-10T00:00:00Z"

# Publication type.
# Legend: 0 = Uncategorized; 1 = Conference paper; 2 = Journal article;
# 3 = Preprint / Working Paper; 4 = Report; 5 = Book; 6 = Book section;
# 7 = Thesis; 8 = Patent
publication_types: ["1"]

# Publication name and optional abbreviated publication name.
publication: "International Symposium on Computer Architecture"
publication_short: "ISCA'25"

abstract: The continuous growth of on-chip transistors driven by technology scaling urges architecture developers to design and implement novel architectures to effectively utilize the excessive on-chip resources.Due to the challenges of programming in register-transfer level (RTL) languages, performance modeling based on cycle-accurate simulation is typically developed alongside hardware implementation, allowing the exploration of high-level design decisions before dealing with the error-prone, low-level RTL details. However, this approach also introduces new challenges in coordinating and aligning separate codebases.In this paper, we address this issue by presenting Assassyn, a unified, high-level, and general-purpose programming framework for architectural simulation and implementation. By taking advantage of asynchronous event handling, a widely existing behavior in both hardware design and implementation and software engineering, a general-purpose, and high-level programming abstraction is proposed to mitigate the difficulties of RTL programming. Moreover, the unified programming interface naturally enables an accurate and faithful alignment between performance modeling and RTL implementation.Our evaluation demonstrates that Assassyn high-level programming interface is sufficiently expressive to support the implementation of a wide range of architectures, including architectural components, application-specific accelerators, and even a CPU. All the generated cycle-accurate simulation models perfectly align with the generated RTL simulations, while achieving 1.4-6× simulation speedup. The generated RTL achieves comparable perf/area compared to handcrafted RTL, and 6× perf/area compared to high-level synthesis generated RTL code.

# Summary. An optional shortened abstract.
summary:

tags:
featured: false

# links:
# - name: ""
#   url: ""
url_pdf: 'https://dl.acm.org/doi/pdf/10.1145/3695053.3731004' 
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