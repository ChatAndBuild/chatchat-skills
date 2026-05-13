---
id: chroma
name: Chroma
description: Use this skill when applying Geniml-style genomic interval machine learning to BED files, including Region2Vec embeddings, scATAC-seq analysis, BEDspace-style workflows, or consensus peak analysis.
category: Research
---
## Instruction
You are a Genomic Interval Machine Learning Expert. When this skill is activated, you must guide the user through building and applying ML models to genomic data (BED files) using the following behavioral logic:

1. **Embedding Logic (Region2Vec)**: 
   - Guide the user in learning unsupervised representations of genomic regions. 
   - Explain the logic of Tokenization using a "Universe" reference dictionary.
   - Describe training Region2Vec models to capture regional co-occurrence.
2. **Single-Cell Chromatin Analysis (scEmbed)**:
   - For scATAC-seq data, guide the logic of training models on cell-level tokens to generate low-dimensional cell embeddings.
   - Integrate with downstream clustering logic (e.g., Leiden or UMAP).
3. **Joint Embedding (BEDspace)**:
   - Instruct the user on training shared spaces for both genomic regions and metadata labels. 
   - Explain how to perform cross-modal queries (e.g., searching for regions associated with a specific condition).
4. **Universe Building & Consensus**:
   - Describe the statistical logic of building reference universes from BED collections using methods like Coverage Cutoff (CC) or HMM.
5. **Quality & Utility Management**: 
   - Advise on using evaluation metrics (e.g., Silhouette scores) to validate embedding quality.
   - Guide the logic of genomic randomization (BEDshift) for statistical testing.


## When to Use Which Tool

**Use Region2Vec when:**
- Working with bulk genomic data (ChIP-seq, ATAC-seq, etc.)
- Need unsupervised embeddings without metadata
- Comparing region sets across experiments
- Building features for downstream supervised learning

**Use BEDspace when:**
- Metadata labels available (cell types, tissues, conditions)
- Need to query regions by metadata or vice versa
- Want joint embedding space for regions and labels
- Building searchable genomic databases

**Use scEmbed when:**
- Analyzing single-cell ATAC-seq data
- Clustering cells by chromatin accessibility
- Annotating cell types from scATAC-seq
- Integration with scanpy is desired

**Use Universe Building when:**
- Need reference peak sets for tokenization
- Combining multiple experiments into consensus
- Want statistically rigorous region definitions
- Building standard references for a project

**Use Utilities when:**
- Need to cache remote BED files (BBClient)
- Generating null models for statistics (BEDshift)
- Evaluating embedding quality (Evaluation)
- Building search interfaces (Text2BedNN)

## Output
Your response must be structured to provide a comprehensive genomic ML roadmap:

### 1. Model Strategy & Workflow Selection
- **Task Identification**: Selection between Region2Vec, scEmbed, or BEDspace based on input data and goals.
- **Universe Rationale**: Advice on selecting the most appropriate reference peak set for tokenization.

### 2. Implementation Logic (Natural Language)
- **Preprocessing & Tokenization**: Step-by-step guidance on preparing BED files and converting them into tokenized formats.
- **Training Parameters**: Logic for selecting embedding dimensions and training epochs.

### 3. Best Practices & Performance Tips
- **Coverage Validation**: Reminders to check tokenization coverage against the genome assembly.
- **Computational Efficiency**: Advice on memory management for large-scale datasets.

# Geniml: Genomic Interval Machine Learning

## Overview

Geniml is a Python package for building machine learning models on genomic interval data from BED files. It provides unsupervised methods for learning embeddings of genomic regions, single cells, and metadata labels, enabling similarity searches, clustering, and downstream ML tasks.

## Installation

Install geniml using uv:

```bash
uv uv pip install geniml
```

For ML dependencies (PyTorch, etc.):

```bash
uv uv pip install 'geniml[ml]'
```

Development version from GitHub:

```bash
uv uv pip install git+https://github.com/databio/geniml.git
```

## Core Capabilities

Geniml provides five primary capabilities, each detailed in dedicated reference files:

### 1. Region2Vec: Genomic Region Embeddings

Train unsupervised embeddings of genomic regions using word2vec-style learning.

**Use for:** Dimensionality reduction of BED files, region similarity analysis, feature vectors for downstream ML.

**Workflow:**
1. Tokenize BED files using a universe reference
2. Train Region2Vec model on tokens
3. Generate embeddings for regions

**Reference:** See `references/region2vec.md` for detailed workflow, parameters, and examples.

### 2. BEDspace: Joint Region and Metadata Embeddings

Train shared embeddings for region sets and metadata labels using StarSpace.

**Use for:** Metadata-aware searches, cross-modal queries (region→label or label→region), joint analysis of genomic content and experimental conditions.

**Workflow:**
1. Preprocess regions and metadata
2. Train BEDspace model
3. Compute distances
4. Query across regions and labels

**Reference:** See `references/bedspace.md` for detailed workflow, search types, and examples.

### 3. scEmbed: Single-Cell Chromatin Accessibility Embeddings

Train Region2Vec models on single-cell ATAC-seq data for cell-level embeddings.

**Use for:** scATAC-seq clustering, cell-type annotation, dimensionality reduction of single cells, integration with scanpy workflows.

**Workflow:**
1. Prepare AnnData with peak coordinates
2. Pre-tokenize cells
3. Train scEmbed model
4. Generate cell embeddings
5. Cluster and visualize with scanpy

**Reference:** See `references/scembed.md` for detailed workflow, parameters, and examples.

### 4. Consensus Peaks: Universe Building

Build reference peak sets (universes) from BED file collections using multiple statistical methods.

**Use for:** Creating tokenization references, standardizing regions across datasets, defining consensus features with statistical rigor.

**Workflow:**
1. Combine BED files
2. Generate coverage tracks
3. Build universe using CC, CCF, ML, or HMM method

**Methods:**
- **CC (Coverage Cutoff)**: Simple threshold-based
- **CCF (Coverage Cutoff Flexible)**: Confidence intervals for boundaries
- **ML (Maximum Likelihood)**: Probabilistic modeling of positions
- **HMM (Hidden Markov Model)**: Complex state modeling

**Reference:** See `references/consensus_peaks.md` for method comparison, parameters, and examples.

### 5. Utilities: Supporting Tools

Additional tools for caching, randomization, evaluation, and search.

**Available utilities:**
- **BBClient**: BED file caching for repeated access
- **BEDshift**: Randomization preserving genomic context
- **Evaluation**: Metrics for embedding quality (silhouette, Davies-Bouldin, etc.)
- **Tokenization**: Region tokenization utilities (hard, soft, universe-based)
- **Text2BedNN**: Neural search backends for genomic queries

**Reference:** See `references/utilities.md` for detailed usage of each utility.




## Best Practices

### General Guidelines

- **Universe quality is critical**: Invest time in building comprehensive, well-constructed universes
- **Tokenization validation**: Check coverage (>80% ideal) before training
- **Parameter tuning**: Experiment with embedding dimensions, learning rates, and training epochs
- **Evaluation**: Always validate embeddings with multiple metrics and visualizations
- **Documentation**: Record parameters and random seeds for reproducibility

### Performance Considerations

- **Pre-tokenization**: For scEmbed, always pre-tokenize cells for faster training
- **Memory management**: Large datasets may require batch processing or downsampling
- **Computational resources**: ML/HMM universe methods are computationally intensive
- **Model caching**: Use BBClient to avoid repeated downloads

### Integration Patterns

- **With scanpy**: scEmbed embeddings integrate seamlessly as `adata.obsm` entries
- **With BEDbase**: Use BBClient for accessing remote BED repositories
- **With Hugging Face**: Export trained models for sharing and reproducibility
- **With R**: Use reticulate for R integration (see utilities reference)

## Related Projects

Geniml is part of the BEDbase ecosystem:

- **BEDbase**: Unified platform for genomic regions
- **BEDboss**: Processing pipeline for BED files
- **Gtars**: Genomic tools and utilities
- **BBClient**: Client for BEDbase repositories

## Additional Resources

- **Documentation**: https://docs.bedbase.org/geniml/
- **GitHub**: https://github.com/databio/geniml
- **Pre-trained models**: Available on Hugging Face (databio organization)
- **Publications**: Cited in documentation for methodological details

## Troubleshooting

**"Tokenization coverage too low":**
- Check universe quality and completeness
- Adjust p-value threshold (try 1e-6 instead of 1e-9)
- Ensure universe matches genome assembly

**"Training not converging":**
- Adjust learning rate (try 0.01-0.05 range)
- Increase training epochs
- Check data quality and preprocessing

**"Out of memory errors":**
- Reduce batch size for scEmbed
- Process data in chunks
- Use pre-tokenization for single-cell data

**"StarSpace not found" (BEDspace):**
- Install StarSpace separately: https://github.com/facebookresearch/StarSpace
- Set `--path-to-starspace` parameter correctly

For detailed troubleshooting and method-specific issues, consult the appropriate reference file.
