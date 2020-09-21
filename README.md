
# SciDD: Scientific Data Descriptors

A Python package for implementing the SciDD data identification scheme and resolving data.

Note: This package is under active development; class names and APIs are subject to change.

## Introduction

Scientific data volumes have increased exponentially which has posed the problem of accessing the data you are looking for. The details of locating relevant data sources, what you want from each source, the format of the data, the means to retrieve it, and how to interpret what you have are mountainous. It's common to find a significant part of analysis code is woven with the nuts and bolts details of downloading files, determining which parts to read, and load them into data structures. Since there often isn't a common interface for all the data sets one might use, the implementation details clutter and distract from the research questions.

The SciDD scheme aims to provide an interface to data by defining descriptors that point to resources that include specific files, rows from a table, an individual column from a single row, or even searches. The design goals include:

* The descriptor is easily generated.
* The descriptor is reasonably human readable.
* The data creator is not required to define the descriptor.
* The descriptor is file/data format agnostic.
* Descriptors are easily citable and searchable.

A journal paper describing the scheme in details is in preparation.

## What Does It Look Like?

There isn't room on this page to demonstrate the full scheme, but a few examples will be provided. 

## Resolvers

It should be apparent from the examples above that the descriptor does not have anything to say about *where* the data is or how to get it: it is only an unambiguous *description* of a particular resource. Converting a descriptor to the resource requires a resolver. This will usually come in the form of a web service (e.g. a REST API), but anything that can performs the task is valid.
