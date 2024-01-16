---
title: "A Convolutional Neural Network Based Maximum Power Point Voltage Forecasting Method for Pavement PV Array"
authors:
  - Mingxuan Mao
  - Xinying Feng
  - admin
  - Tommy W. S. Chow

date: "2022-11-08T00:00:00Z"
doi: "10.1109/TIM.2022.3227552"

# Schedule page publish date (NOT publication's date).
publishDate: "2022-11-08T00:00:00Z"

# Publication type.
# Legend: 0 = Uncategorized; 1 = Conference paper; 2 = Journal article;
# 3 = Preprint / Working Paper; 4 = Report; 5 = Book; 6 = Book section;
# 7 = Thesis; 8 = Patent
publication_types: ["2"]

# Publication name and optional abbreviated publication name.
publication: "*IEEE Transactions on Instrumentation and Measurement 2022*"
publication_short: "TIM'22 (JCR Q1)"

abstract: The shadows formed by fast-moving vehicles on a pavement PV array exhibit complex dynamic random distribution characteristics, which can cause a dynamic multipeak PV curve. Dynamic vehicle shadow will cause a reduction in pavement PV power, so the question is how to maximize the power in such conditions by operating at different maximum power point (MPP) quickly and continually. To address this issue, this article proposes an MPP voltage forecasting method based on convolutional neural network (CNN). This method inputs the environmental information of pavement PV array into the proposed CNN model for learning and then uses this model to forecast the MPP voltage. Finally, simulation and experimental test with ResNet, MLP, and CNN methods are carried out and the comparison results show that this model can accurately predict the MPP voltage of pavement PV array under different vehicle shading conditions.

# Summary. An optional shortened abstract.
summary: In this article, we propose a prediction model method for the MPP voltage based on CNN. First, the CNN voltage prediction model is constructed by comparing the performance of the different neural network algorithms with the different convolution kernel sizes. The image information of the pavement PV array is then used as the input, and we use the CNN model to forecast its MPP voltage in a short amount of time. Finally, a series of simulation and experimental tests are done, and the prediction results of the MPP voltage under different shading conditions show that the proposed prediction model can effectively predict the MPP voltage of pavement PV array in a robust way.

tags:
featured: false

# links:
# - name: ""
#   url: ""
url_pdf: https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=9975320
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