---
# Leave the homepage title empty to use the site title
title:
date: 2023-05-14
type: landing

sections:
  - block: about.avatar
    id: about
    content:
      # Choose a user profile to display (a folder name within `content/authors/`)
      username: JihaoCH
      # Override your bio text from `authors/admin/_index.md`?
      text:
  - block: collection
    id: publication
    content:
      title: 论文
      text: |-
        {{% callout note %}}
        单击 [此处](./publication/) 快速检索.
        {{% /callout %}}
      filters:
        folders:
          - publication
        exclude_featured: false
    design:
      columns: '2'
      view: citation
  - block: experience
    id: education
    content:
      title: 学历
      # Date format for experience
      #   Refer to https://wowchemy.com/docs/customization/#date-format
      date_format: Jan 2006
      # Experiences.
      #   Add/remove as many `experience` items below as you like.
      #   Required fields are `title`, `company`, and `date_start`.
      #   Leave `date_end` empty if it's your current employer.
      #   Begin multi-line descriptions with YAML's `|2-` multi-line prefix.
      items:
        - title: 计算机科学 博士在读
          company: 阿卜杜拉国王科技大学
          company_url: https://www.kaust.edu.sa
          company_logo: KAUST
          location: 沙特阿拉伯 麦加省 图瓦
          date_start: '2023-01-01'
          date_end:
        - title: "计算机科学 硕士 GPA 3.90/4.0 院长嘉许名单"
          company: 阿卜杜拉国王科技大学 
          company_url: https://www.kaust.edu.sa
          company_logo: KAUST
          location: "沙特阿拉伯 麦加省 图瓦"
          date_end: '2022-12-01'
          date_start: '2021-08-01'
        - title: 应用计算科学与工程 硕士 一等学位
          company: 帝国理工学院
          company_url: https://www.imperial.ac.uk
          company_logo: ICL
          location: 英国 伦敦
          date_end: '2021-10-01'
          date_start: '2020-10-01'
        - title: "计算机科学与技术 学士 GPA 89.34/100"
          company: 山东大学 
          company_url: https://www.sdu.edu.cn
          company_logo: SDU
          location: 山东省 威海
          date_end: '2020-06-01'
          date_start: '2016-09-01'
    design:
      columns: '2'
  - block: experience
    id: internship
    content:
      title: 实习
      # Date format for experience
      #   Refer to https://wowchemy.com/docs/customization/#date-format
      date_format: Jan 2006
      # Experiences.
      #   Add/remove as many `experience` items below as you like.
      #   Required fields are `title`, `company`, and `date_start`.
      #   Leave `date_end` empty if it's your current employer.
      #   Begin multi-line descriptions with YAML's `|2-` multi-line prefix.
      items:
        - title: 研究实习生
          company: 微软亚洲研究院
          company_url: ''
          company_logo: microsoft
          location: 北京 中国
          date_start: '2023-09-12'
          date_end: ''
          description:

        - title: 研究实习生
          company: 奥地利科学技术研究所
          company_url: ''
          company_logo: ista
          location: 奥地利 维也纳
          date_start: '2022-05-01'
          date_end: '2022-08-01'
          description: |
              基于高效阈值选择的TopK梯度压缩。 语言：CUDA/C++
              
        - title: 后端开发实习生
          company: Tencent Cloud
          company_url: ''
          company_logo: tencent
          location: 中国 深圳
          date_start: '2019-08-01'
          date_end: '2019-11-01'
          description: |
           腾讯国际站后台开发。 语言：GoLang

        - title: 研究实习生
          company: 西澳大利亚大学
          company_url: ''
          company_logo: uwa
          location: 远程
          date_start: '2019-06-01'
          date_end: '2019-08-01'
          description: |
           基于YOLO的西澳大利亚环海高速浪花监测。语言：Python

    design:
      columns: '2'
  - block: accomplishments
    id: experience
    content:
      # Note: `&shy;` is used to add a 'soft' hyphen in a long heading.
      title: '其他'
      subtitle:
      # Date format: https://wowchemy.com/docs/customization/#date-format
      date_format: Jan 2006
      # Accomplishments.
      #   Add/remove as many `item` blocks below as you like.
      #   `title`, `organization`, and `date_start` are the required parameters.
      #   Leave other parameters empty if not required.
      #   Begin multi-line descriptions with YAML's `|2-` multi-line prefix.
      items:
        - certificate_url:
          date_end: ''
          date_start: '2023-07-01'
          description: ''
          organization: KAUST
          organization_url: https://www.kaust.org
          title: 助教 - 电子科大 & KAUST 暑校
          url: 
        - certificate_url:
          date_end: '2022-12-01'
          date_start: '2022-08-01'
          description: ''
          organization: KAUST
          organization_url: https://www.kaust.org
          title: "助教 - KAUST CS240 : 并发计算系统"
          url: 'https://sands.kaust.edu.sa/classes/CS240/F22/'
        - certificate_url:
          date_end: ''
          date_start: '2022-06-01'
          description: ''
          organization: KAUST
          organization_url: https://www.kaust.org
          title: 助教 - 电子科大 & KAUST 暑校
          url: 
        - certificate_url:
          date_start: '2019-01-01'
          date_end: '2019-02-01'
          description: ''
          organization: ICL
          organization_url: https://www.ic.ac.uk
          title: "帝国理工哈姆林中心机器人与AI寒校"
          url: 

    design:
      columns: '2'
  # - block: accomplishments
  #   id: award
  #   content:
  #     # Note: `&shy;` is used to add a 'soft' hyphen in a long heading.
  #     title: '奖项'
  #     subtitle:
  #     # Date format: https://wowchemy.com/docs/customization/#date-format
  #     date_format: Jan 2006
  #     # Accomplishments.
  #     #   Add/remove as many `item` blocks below as you like.
  #     #   `title`, `organization`, and `date_start` are the required parameters.
  #     #   Leave other parameters empty if not required.
  #     #   Begin multi-line descriptions with YAML's `|2-` multi-line prefix.
  #     items:
  #       - certificate_url:
  #         date_end: ''
  #         date_start: '2023-08-24'
  #         description: ''
  #         organization: KAUST
  #         organization_url: https://www.kaust.org
  #         title: 院长嘉许名单
  #         url: 


    design:
      columns: '2'
  - block: features
    id: like
    content:
      title: 专注于 ...
      items:
        - name: Linux
          icon: linux
          icon_pack: fab
        - name: C++/CUDA
          icon: c
          icon_pack: fab
        - name: Python/PyTorch
          icon: python
          icon_pack: fab

  - block: markdown
    id: kaust
    content:
      title: KAUST剪影
      subtitle: ''
      text: |-
        {{< gallery album="demo" >}}
    design:
      columns: '1'

  - block: contact
    id: contact
    content:
      title: Contact
      subtitle:
      text: |-
      # Contact (add or remove contact options as necessary)
      phone: +966560569149
      address:
        street: KAUST
        city: 图瓦
        region: 麦加省
        postcode: '23955'
        country: 沙特阿拉伯
        country_code: SA
      directions: 4307-WS18, 1号楼海景侧四楼
      # Automatically link email and phone or display as text?
      # autolink: false
      # # Email form provider
      # form:
      #   provider: netlify
      #   formspree:
      #     id:
      #   netlify:
      #     # Enable CAPTCHA challenge to reduce spam?
      #     captcha: yes
    design:
      columns: '2'
---
