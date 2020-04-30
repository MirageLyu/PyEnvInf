# PyEnvInf
A tool helps solve env dependencies for python snippets

## DependencyGraphBuilder
- Download Dockerfile/Requirements source files
- Data cleaning
- Run Dockerfile/Requirements Parser, extract packages

## AssociationAnalysis
Process packages data using Association rules mining methods, and generate json file.
- fpgrowth
- apriori
- Fast fpgrowth

## Inference
- Infer env dependencies from graph database using dfs.
- generate new Dockerfile/Requirements

## neo4j
generated graph database.