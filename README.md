# AnaliTexGra

## Overview

AnaliTexGra is a web application developed with Dash, a Python framework for building interactive data-driven applications.

The application supports the exploration and analysis of academic collaboration data through an interactive interface. It integrates graph visualization, link prediction, text mining, and scientometric analysis to support the study of co-authorship networks and potential research collaborations.

An anonymized institutional dataset is included in the repository to allow the application and the associated analyses to be reproduced.

## Dataset

The anonymized dataset included in the repository is located at:

```text
datasets/UNAM_Completo_Corregido_Anonimizado.csv
```

The dataset contains bibliographic and academic metadata used to construct the collaboration network and to support the structural and textual analyses implemented in AnaliTexGra.

## Requirements

The project uses a Conda environment. The complete software dependencies and exact library versions are specified in:

```text
environment.yml
```

The environment uses:

```text
Python 3.10.18
```

Main libraries include:

- Dash
- pandas
- NumPy
- scikit-learn
- NetworkX
- Plotly
- TensorFlow
- PyTorch
- PyTorch Geometric

The exact versions of these and all additional dependencies are specified in `environment.yml`.

## Installation

Clone the repository:

```bash
git clone https://github.com/pilarang/AnaliTexGra.git
cd AnaliTexGra
```

Create the Conda environment:

```bash
conda env create -f environment.yml
```

Activate the environment:

```bash
conda activate EnvGraphAcademicos
```

## How to Run the Application

Run:

```bash
python app.py
```

Then open the URL displayed by Dash in your browser, usually:

```text
http://127.0.0.1:8050
```

## Reproducibility

The repository provides:

- the anonymized institutional dataset used by the public version of AnaliTexGra;
- the source code of the application;
- the scripts and computational components used for structural, textual, and link-prediction analyses; and
- the complete Conda environment specification with exact software versions.

The public anonymized dataset is:

```text
datasets/UNAM_Completo_Corregido_Anonimizado.csv
```

The computational environment is specified in:

```text
environment.yml
```

Git is used for version control so that the exact version of the code associated with experimental results can be identified through a commit hash.

The current commit identifier can be obtained with:

```bash
git rev-parse HEAD
```

## Notes

AnaliTexGra is built using Dash, a Flask-based framework for creating interactive web applications in Python.

For more information about Dash, visit:

https://dash.plotly.com/

## Contact

For further information or questions:

pilarang@unam.mx
