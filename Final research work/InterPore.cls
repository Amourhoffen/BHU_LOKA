\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{InterPore}[2026/01/01 InterPore Journal Article Class]

\DeclareOption{OA}{}
\DeclareOption{linenum}{\PassOptionsToPackage{lineno}{lineno}}
\DeclareOption{doublespace}{\PassOptionsToPackage{doublespace}{setspace}}
\DeclareOption{suppleart}{}
\DeclareOption{CCBY}{}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax

\LoadClass[10pt,a4paper]{article}

\RequirePackage[utf8]{inputenc}
\RequirePackage[T1]{fontenc}
\RequirePackage{geometry}
\geometry{top=2.2cm, bottom=2.2cm, left=2.0cm, right=2.0cm}
\RequirePackage{amsmath,amssymb,amsfonts}
\RequirePackage{graphicx}
\RequirePackage{xcolor}
\RequirePackage{hyperref}
\RequirePackage{booktabs}
\RequirePackage{caption}
\RequirePackage{subcaption}
\RequirePackage{natbib}
\RequirePackage{url}
\RequirePackage{fancyhdr}

\definecolor{interporeblue}{RGB}{0,115,152}
\definecolor{interporeorange}{RGB}{235,100,20}

\hypersetup{
    colorlinks=true,
    linkcolor=interporeblue,
    citecolor=interporeblue,
    urlcolor=interporeblue
}

% Editorial Office metadata commands
\newcommand{\artcategory}[1]{\def\@artcategory{#1}}
\newcommand{\vol}[1]{\def\@vol{#1}}
\newcommand{\iss}[1]{\def\@iss{#1}}
\newcommand{\cpyear}[1]{\def\@cpyear{#1}}
\newcommand{\doi}[1]{\def\@doi{#1}}
\newcommand{\recdate}[1]{\def\@recdate{#1}}
\newcommand{\accdate}[1]{\def\@accdate{#1}}
\newcommand{\pubdate}[1]{\def\@pubdate{#1}}
\newcommand{\vordate}[1]{\def\@vordate{#1}}
\newcommand{\rhauthor}[1]{\def\@rhauthor{#1}}
\newcommand{\citethisarticle}[1]{\def\@citethisarticle{#1}}
\newcommand{\orc}[1]{\href{https://orcid.org/#1}{\textcolor{interporeblue}{[#1]}}}
\newcommand{\email}[1]{\href{mailto:#1}{\texttt{#1}}}

\renewcommand{\author}[2][]{\g@addto@macro\@authorlines{\textbf{#2}\textsuperscript{#1}\quad }}
\newcommand{\@authorlines}{}
\newcommand{\affil}[2][]{\g@addto@macro\@affillines{\textsuperscript{#1}\textit{#2}\\} }
\newcommand{\@affillines}{}
\newcommand{\corau}[1]{\def\@corau{#1}}
\renewcommand{\abstract}[1]{\def\@abstract{#1}}
\newcommand{\keyword}[1]{\def\@keyword{#1}}
\newcommand{\whypapermatters}[1]{\def\@whypapermatters{#1}}

\renewcommand{\maketitle}{%
    \begin{center}
        \vspace*{-1cm}
        {\raggedright \textbf{\color{interporeorange}\MakeUppercase{\@artcategory}} \hfill \small \textit{InterPore Journal} | \@cpyear\par}
        \vspace{0.4em}\hrule height 1.5pt \vspace{1em}
        {\LARGE \bfseries \@title \par}
        \vspace{1.2em}
        {\large \@authorlines \par}
        \vspace{0.8em}
        {\small \@affillines \par}
        \vspace{0.5em}
        \ifdefined\@corau
        {\footnotesize \textbf{*Correspondence:} \@corau \par}
        \fi
    \end{center}
    \vspace{1em}
    \begin{center}
        \begin{minipage}{0.96\textwidth}
            \hrule height 0.5pt \vspace{0.8em}
            {\small \textbf{Abstract:} \@abstract \par}
            \vspace{0.6em}
            {\small \textbf{Keywords:} \@keyword \par}
            \ifdefined\@whypapermatters
            \vspace{0.6em}
            {\small \textbf{Why This Paper Matters:} \textit{\@whypapermatters} \par}
            \fi
            \vspace{0.8em}\hrule height 0.5pt
        \end{minipage}
    \end{center}
    \vspace{1.5em}
}

% Boxed figure environment
\newenvironment{boxedfigure}[2][]{%
    \begin{figure}[#1]
    \centering
    \begin{minipage}{#2}
    \centering
}{%
    \end{minipage}
    \end{figure}
}

% Table helpers
\newcommand{\tbl}[2]{\caption{#1}#2}
\newcommand{\rowrule}{\midrule}
\newcommand{\TCH}{}

% Statements and Declarations environments
\newenvironment{bmsec}[1][]{\vspace{0.8em}\noindent\textbf{#1:}\par\noindent}{\vspace{0.8em}}
\newenvironment{datres}{\vspace{0.8em}\noindent\textbf{Data and Code Availability:}\par\noindent}{\vspace{0.8em}}
\newenvironment{ack}{\vspace{0.8em}\noindent\textbf{Acknowledgements:}\par\noindent}{\vspace{0.8em}}

\newenvironment{orcaulist}{\vspace{0.5em}\noindent\textbf{ORCID Identifiers:}\begin{itemize}}{\end{itemize}}
\newcommand{\orcaulistitem}[2][]{\item #2: \url{https://orcid.org/#1}}

\endinput
