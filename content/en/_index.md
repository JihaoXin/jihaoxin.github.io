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
      username: admin
      # Override your bio text from `authors/admin/_index.md`?
      text:
  - block: collection
    id: publication
    content:
      title: Paper
      text: |-
        {{% callout note %}}
        Quickly discover relevant content by [filtering papers](./publication/).
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
      title: Education
      # Date format for experience
      #   Refer to https://wowchemy.com/docs/customization/#date-format
      date_format: Jan 2006
      # Experiences.
      #   Add/remove as many `experience` items below as you like.
      #   Required fields are `title`, `company`, and `date_start`.
      #   Leave `date_end` empty if it's your current employer.
      #   Begin multi-line descriptions with YAML's `|2-` multi-line prefix.
      items:
        - title: Ph.D. student in Computer Science
          company: KAUST
          description: |2-
            * KAUST Graduate Student Council Representative (12/1683) (2024-2025)
            * TA-KAUST CS240: Computing Systems and Concurrency (2022 Fall, 2024Fall)
            * TA-Saudi Ministry of Interior Program CS229: Machine Learning (2023 Spring)
            * TA-UESTC Boot Camp (2022 Summer, 2023 Summer)
            * TA-CS398 Graduate Seminar (2025 Spring)
          company_url: https://www.kaust.edu.sa
          company_logo: KAUST
          location: Thuwal, Saudi Arabia
          date_start: '2023-01-01'
          date_end:
        - title: Master of Science in Computer Science
          company: KAUST
          description: |2-
            * Dean's List Award (2023)
            * GPA = 3.88/4.0
          company_url: https://www.kaust.edu.sa
          company_logo: KAUST
          location: "Thuwal, Saudi Arabia"
          date_end: '2022-12-01'
          date_start: '2021-08-01'
        - title: Master of Science in Applied Computational Science and Engineering  (Distinction)
          company: Imperial College London
          company_url: https://www.imperial.ac.uk
          company_logo: ICL
          location: London, UK
          date_end: '2021-10-01'
          date_start: '2020-10-01'
        - title: Bachelor of Engineering in Computer Science and Technology (GPA = 89.34/100)
          company: Shandong University
          company_url: https://www.sdu.edu.cn
          company_logo: SDU
          location: Weihai, China
          date_end: '2020-06-01'
          date_start: '2016-09-01'
    design:
      columns: '2'
  - block: experience
    id: internship
    content:
      title: Internship
      # Date format for experience
      #   Refer to https://wowchemy.com/docs/customization/#date-format
      date_format: Jan 2006
      # Experiences.
      #   Add/remove as many `experience` items below as you like.
      #   Required fields are `title`, `company`, and `date_start`.
      #   Leave `date_end` empty if it's your current employer.
      #   Begin multi-line descriptions with YAML's `|2-` multi-line prefix.
      items:
        - title: Research Intern
          company: Microsoft Research Asia
          company_url: ''
          company_logo: microsoft
          location: Beijing, China
          date_start: '2023-09-19'
          date_end: '2024-03-19'
          description:
        - title: Research Intern
          company: ISTAustria
          company_url: ''
          company_logo: ista
          location: Klosterneuburg, Austria
          date_start: '2022-05-01'
          date_end: '2022-08-01'
          description: |
              TopK gradient compression with efficient threshold selection by CUDA/C++.
              
        - title: Engineering Intern
          company: Tencent Cloud
          company_url: ''
          company_logo: tencent
          location: Shenzhen, China
          date_start: '2019-08-01'
          date_end: '2019-11-01'
          description: |
           Tencent international website backend developer by GoLang.

        - title: Research Intern
          company: The University of Western Australia
          company_url: ''
          company_logo: uwa
          location: Remote
          date_start: '2019-06-01'
          date_end: '2019-08-01'
          description: |
           YOLO-based splash detection of Western Australia's coastal highway by Python.

    design:
      columns: '2'
  - block: accomplishments
    id: experience
    content:
      # Note: `&shy;` is used to add a 'soft' hyphen in a long heading.
      title: 'Experience'
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
          date_start: '2019-06-01'
          date_end: '2019-08-01'
          organization: uwa
          organization_url: ''
          title: "Summer Research Program - The University of Western Australia"
          url: ''
        - certificate_url:
          date_start: '2019-01-01'
          date_end: '2019-02-01'
          description: ''
          organization: ICL
          organization_url: https://www.ic.ac.uk
          title: "Robotics & AI Winter School - Imperial College London Hamlyn Center"
          url: 
 

  #   design:
  #     columns: '2'
  # - block: accomplishments
  #   id: award
  #   content:
  #     # Note: `&shy;` is used to add a 'soft' hyphen in a long heading.
  #     title: 'Award'
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
  #         title: Dean's List Award
  #         url: 

    design:
      columns: '2'
  - block: features
    id: like
    content:
      title: I'm into ...
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
      title: Gallery of KAUST
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
        street: KAUST Campus
        city: Thuwal
        region: Mekka Province
        postcode: '23955'
        country: Saudi Arabia
        country_code: SA
      directions: 4307-WS18, 4th Floor, Building 1
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
