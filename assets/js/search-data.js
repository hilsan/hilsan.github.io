// get the ninja-keys element
const ninja = document.querySelector('ninja-keys');

// add the home and posts menu items
ninja.data = [{
    id: "nav-about",
    title: "about",
    section: "Navigation",
    handler: () => {
      window.location.href = "/";
    },
  },{id: "nav-cv",
          title: "CV",
          description: "",
          section: "Navigation",
          handler: () => {
            window.location.href = "/cv/";
          },
        },{id: "nav-news",
          title: "news",
          description: "",
          section: "Navigation",
          handler: () => {
            window.location.href = "/news/index.html";
          },
        },{id: "nav-publications",
          title: "publications",
          description: "Publications in reversed chronological order. My name is underlined.",
          section: "Navigation",
          handler: () => {
            window.location.href = "/publications/";
          },
        },{id: "nav-talks",
          title: "talks",
          description: "",
          section: "Navigation",
          handler: () => {
            window.location.href = "/talks/";
          },
        },{id: "nav-teaching-portfolio",
          title: "teaching portfolio",
          description: "",
          section: "Navigation",
          handler: () => {
            window.location.href = "/teaching/";
          },
        },{id: "nav-outreach",
          title: "outreach",
          description: "",
          section: "Navigation",
          handler: () => {
            window.location.href = "/outreach/";
          },
        },{id: "news-awarded-a-marie-skłodowska-curie-actions-msca-postdoctoral-fellowship-202-125-for-the-cloudmap-project-at-tu-munich-read-more",
          title: 'Awarded a Marie Skłodowska-Curie Actions (MSCA) Postdoctoral Fellowship (€202,125) for the CLOUDMAP project...',
          description: "",
          section: "News",},{id: "news-new-paper-published-in-geoscientific-model-development-similarity-based-analysis-of-atmospheric-organic-compounds-for-machine-learning-applications-read-more",
          title: 'New paper published in Geoscientific Model Development: Similarity-based analysis of atmospheric organic compounds...',
          description: "",
          section: "News",},{id: "news-starting-my-2-year-msca-funded-project-cloudmap-at-tum-read-more",
          title: 'Starting my 2-year MSCA-funded project CLOUDMAP at TUM! Read more →',
          description: "",
          section: "News",},{id: "news-congratulations-to-linus-lind-on-his-graduation-his-work-on-molecular-descriptors-for-atmospheric-compounds-is-now-available-as-a-preprint-read-more",
          title: 'Congratulations to Linus Lind on his graduation! His work on molecular descriptors for...',
          description: "",
          section: "News",},{id: "news-thesis-reviewer-and-opponent-at-universitat-autònoma-de-barcelona-uab-barcelona-spain",
          title: 'Thesis reviewer and opponent at Universitat Autònoma de Barcelona (UAB), Barcelona, Spain.',
          description: "",
          section: "News",},{id: "news-first-time-thesis-opponent-in-barcelona-for-niccolò-bancone-uab-and-linus-first-first-author-paper-published-read-more",
          title: 'First time thesis opponent in Barcelona for Niccolò Bancone (UAB), and Linus’ first...',
          description: "",
          section: "News",},{id: "news-contributed-talk-at-ccsc-2026-munich-germany-towards-atmospheric-compound-identification-using-simulated-electron-ionization-mass-spectra",
          title: 'Contributed talk at CCSC 2026 (Munich, Germany): Towards atmospheric compound identification using simulated...',
          description: "",
          section: "News",},{id: "news-invited-talk-at-the-university-of-glasgow-network-on-mathematical-data-science-for-materials-science-workshop-data-driven-compound-identification-with-atmospheric-mass-spectrometry",
          title: 'Invited talk at the University of Glasgow (Network on Mathematical Data Science for...',
          description: "",
          section: "News",},{
      id: 'light-theme',
      title: 'Change theme to light',
      description: 'Change the theme of the site to Light',
      section: 'Theme',
      handler: () => {
        setThemeSetting("light");
      },
    },
    {
      id: 'dark-theme',
      title: 'Change theme to dark',
      description: 'Change the theme of the site to Dark',
      section: 'Theme',
      handler: () => {
        setThemeSetting("dark");
      },
    },
    {
      id: 'system-theme',
      title: 'Use system default theme',
      description: 'Change the theme of the site to System Default',
      section: 'Theme',
      handler: () => {
        setThemeSetting("system");
      },
    },];
