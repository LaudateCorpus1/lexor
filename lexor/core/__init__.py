"""Core

The core of lexor is divided among the packages in this module.

## elements

Provides the basic structures to handle the information provided in
files. Make sure to familiarize yourself with all the objects in this
module to be able to write extensions for the `Parser`, `Converter`
and `Writer`.

## parser

The parser module provides the `Parser` and the abstract class
`NodeParser` which helps us write derived objects for future languages
to parse.

## converter

The converter module provides the `Converter` and the abstract class
`NodeConverter` which helps us copy a `Document` we want to convert
to another language.

## writer

The writer module provides the `Writer` and the abstract class
`NodeWriter` which once subclassed help us tell the `Writer` how to
write a `Node` to a `file` object.

"""
