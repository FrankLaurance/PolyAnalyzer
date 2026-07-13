# PolyAnalyzer Domain Context

PolyAnalyzer turns instrument export files into repeatable polymer-characterization outputs through desktop and command-line workflows.

## Language

**Analysis**:
A configured run that transforms one or more selected instrument files into material-characterization outputs.
_Avoid_: Job, task, process

**Analyzer**:
The domain module that parses one instrument format and produces the outputs for one analysis kind.
_Avoid_: Handler, processor

**Analysis Profile**:
A named collection of plotting and calculation choices reusable across analyses.
_Avoid_: Setting file, preset

**Analysis Output**:
The complete set of files committed by one successful analysis.
_Avoid_: Result folder, generated files

## Relationships

- An **Analysis** selects exactly one **Analyzer**
- An **Analysis** consumes one or more instrument files
- An **Analysis** may use one **Analysis Profile**
- A successful **Analysis** commits one **Analysis Output**
- A failed **Analysis** preserves the previous **Analysis Output**

## Example dialogue

> **Developer:** "Should an **Analysis** replace the existing **Analysis Output** as each image is written?"
> **Domain expert:** "No. Commit the complete **Analysis Output** only after the **Analyzer** finishes successfully."

## Flagged ambiguities

- "settings" previously meant both transient UI state and reusable files; reusable named values are **Analysis Profiles**.
