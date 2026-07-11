\ProvidesClass{resume}[2025/01/31 v1.0 Professional Resume Class]

\LoadClass[11pt,letterpaper]{article} % 设置字体大小和纸张格式

%----------------------------------------
%           基础导入包
%----------------------------------------
\usepackage[left=0.8in,top=0.5in,right=0.8in,bottom=0.5in]{geometry} % 调整页边距
\usepackage{parskip} % 段落无缩进
\usepackage{array} % 表格增强
\usepackage{ifthen} % 逻辑判断
\usepackage{titlesec} % 自定义标题样式
\usepackage{xcolor} % 颜色支持
\usepackage{enumitem} % 自定义列表

\pagestyle{empty} % 取消页码

%----------------------------------------
%           标题样式
%----------------------------------------
\titleformat{\section}
  {\large\bfseries\uppercase}{\thesection}{1em}{} % 标题加粗 + 大写

%----------------------------------------
%           个人信息
%----------------------------------------
\def \name#1{\def\@name{#1}}
\def \@name {}
\def \addressSep {\quad$\cdot$\quad} % 地址信息间隔符

\let \@addressone \relax
\let \@addresstwo \relax
\let \@addressthree \relax

\def \address #1{
  \@ifundefined{@addresstwo}{
    \def \@addresstwo {#1}
  }{
  \@ifundefined{@addressthree}{
  \def \@addressthree {#1}
  }{
     \def \@addressone {#1}
  }}
}

\def \printaddress #1{
  \begingroup
    \def \\ {\addressSep\ }
    \centerline{\small #1} % 让地址小一号
  \endgroup
  \par
  \smallskip
}

\def \printname {
  \begingroup
    \hfil{\LARGE\bfseries \@name}\hfil % 姓名加粗 & 更大字号
    \bigskip\break
  \endgroup
}

%----------------------------------------
%           文档开始
%----------------------------------------
\let\ori@document=\document
\renewcommand{\document}{
  \ori@document
  \printname
  \@ifundefined{@addressone}{}{\printaddress{\@addressone}}
  \@ifundefined{@addresstwo}{}{\printaddress{\@addresstwo}}
  \@ifundefined{@addressthree}{}{\printaddress{\@addressthree}}
}

%----------------------------------------
%           段落格式
%----------------------------------------
\newcommand{\sectionline}{\hrule height 0.5pt} % 加细分隔线

%----------------------------------------
%           主要结构
%----------------------------------------
\newenvironment{rSection}[1]{ % 标题格式
  \medskip
  {\Large\bfseries \MakeUppercase{#1}} % 标题大写
  \smallskip
  \sectionline
  \begin{list}{}{ \setlength{\leftmargin}{1.5em} }
  \item[]
}{
  \end{list}
}

%----------------------------------------
%           工作经验 & 项目格式
%----------------------------------------
\newenvironment{rSubsection}[4]{ % 4个参数：项目名称，时间，职位，机构
 {\bf #1} \hfill {#2} % 项目名称加粗，时间靠右
 \ifthenelse{\equal{#3}{}}{}{ % 如果职位不为空，则换行
  \\
  {\em #3} \hfill {\em #4} % 职位斜体
  }
  \vspace{-0.3em}
  \begin{list}{$\bullet$}{\leftmargin=1.5em \itemsep -0.3em} % 更紧凑的列表
}{
  \end{list}
  \vspace{0.3em}
}

%----------------------------------------
%           个人信息样式
%----------------------------------------
\def\namesize{\huge} % 顶部姓名字号
\def\addressskip{\smallskip} % 地址间距
\def\sectionlineskip{\medskip} % 标题间距
\def\nameskip{\bigskip} % 姓名后间距
\def\sectionskip{\medskip} % 段落间距