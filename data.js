// File System Structure
const rootFileSystem = {
  type: "dir",
  children: {
    "Research": {
      type: "dir",
      description: "Academic Research",
      children: {
        "Global_Parameterization": {
          type: "paper",
          title: "Global Parameterization from Prescribed Holonomy Signatures",
          authors: "Hanxiao Shen, Leyi Zhu, Ryan Capouellez, Daniele Panozzo, Marcel Campen, Denis Zorin",
          venue: "ACM Trans. Graph. (SIGGRAPH 2022)",
          link: "http://graphics.cs.uos.de/papers/Holonomy_Signature_Parametrization-SIGGRAPH2022_Preprint.pdf",
          image: "./quadragulation.png",
          abstract: "We describe a method for the generation of seamless surface parametrizations with guaranteed local injectivity and full control over holonomy."
        },
        "Discrete_Conformal_Equivalence": {
          type: "paper",
          title: "Efficient and Robust Discrete Conformal Equivalence with Boundary",
          authors: "Marcel Campen, Ryan Capouellez, Hanxiao Shen, Leyi Zhu, Daniele Panozzo, Denis Zorin",
          venue: "SIGGRAPH Asia 2021",
          link: "https://cims.nyu.edu/gcl/papers/2021-Conformal.pdf",
          image: "./conformal.png",
          abstract: "We present a method for computing discrete conformal equivalence of triangle meshes with boundary based on the theory of discrete conformal geometry."
        },
        "MPM_Fracture": {
          type: "paper",
          title: "Simulation and visualization of ductile fracture with the material point method",
          authors: "S Wang, M Ding, TF Gast, L Zhu, S Gagniere, C Jiang, JM Teran",
          venue: "Proc. ACM Comput. Graph. Interact. Tech. (2019)",
          link: "https://stephaniewang.page/files/fracture_paper.pdf",
          image: "./fracture.png",
          abstract: "We present a Material Point Method (MPM) for simulating ductile fracture using a new yield criterion.",
          award: "SCA 2018 Best Paper Award"
        },
        "scholar_profile": {
          type: "link",
          url: "https://scholar.google.com/citations?user=ZZJP2N4AAAAJ&hl=en&oi=ao",
          description: "Google Scholar Profile"
        }
      }
    },
    "Playground": {
      type: "dir",
      description: "Fun & Demos",
      children: {
        "fish": { type: "link", url: "fish.html", description: "Moyu Workspace(摸鱼模拟器) 🐟" },
        "XmasTreeGen": { type: "link", url: "xmas.html", description: "A Christmas Tree 🎄 generator" },
        "XmasDrill3000": { type: "link", url: "xmasgm1.html", description: "Christmas Drill 3000 🌀 for my dear friend gm1" }
        // "demogorgon": { type: "link", url: "demogorgon.html", description: "The Upside Down 👹" }
      }
    },
    "about": {
      type: "text",
      content: `Identity: Leyi (zlyfunction)
----------------------------------------
> Fueling my code with Brown Sugar Boba Tea 🧋
> Exploring the elegant beauty of geometry 📐
> Researching Geometry Processing & Computer Graphics 💻`
    },
    "contact": {
      type: "text",
      content: `Email: leyi *AT* nyu.edu
Feel free to reach out for collaborations or boba tea recommendations!`
    }
  }
};

// Themes Configuration
const themes = {
  default: {
    '--bg-color': '#0d1117',
    '--text-color': '#c9d1d9',
    '--prompt-color': '#58a6ff',
    '--command-color': '#f0f6fc',
    '--result-color': '#8b949e',
    '--highlight-color': '#7ee787',
    '--error-color': '#ff7b72',
    '--link-color': '#79c0ff',
    '--border-color': '#30363d',
    '--glow-color': 'rgba(88, 166, 255, 0.3)'
  },
  hacker: {
    '--bg-color': '#000000',
    '--text-color': '#00ff00',
    '--prompt-color': '#00ff00',
    '--command-color': '#ccffcc',
    '--result-color': '#00cc00',
    '--highlight-color': '#00ff00',
    '--error-color': '#ff0000',
    '--link-color': '#00ff00',
    '--border-color': '#003300',
    '--glow-color': 'rgba(0, 255, 0, 0.4)'
  },
  retro: {
    '--bg-color': '#1a1a1a',
    '--text-color': '#ffb000',
    '--prompt-color': '#ffb000',
    '--command-color': '#ffe082',
    '--result-color': '#ffca28',
    '--highlight-color': '#ffb000',
    '--error-color': '#ff5252',
    '--link-color': '#ffb000',
    '--border-color': '#3e2723',
    '--glow-color': 'rgba(255, 176, 0, 0.4)'
  },
  dracula: {
    '--bg-color': '#282a36',
    '--text-color': '#f8f8f2',
    '--prompt-color': '#bd93f9',
    '--command-color': '#f8f8f2',
    '--result-color': '#6272a4',
    '--highlight-color': '#50fa7b',
    '--error-color': '#ff5555',
    '--link-color': '#8be9fd',
    '--border-color': '#44475a',
    '--glow-color': 'rgba(189, 147, 249, 0.3)'
  }
};