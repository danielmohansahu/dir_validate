""" Convenience function wrappers around core Template operations.
"""

# future
from __future__ import annotations

# STL
import typing
import argparse

# YAML
import yaml

# Custom
from .template import Template

def parse_args():
    parser = argparse.ArgumentParser("VALIDate DIRectory structures from a pre-defined template.")
    subparsers = parser.add_subparsers(help="commands")

    validate_parser = subparsers.add_parser('validate', help='Validate a given directory.')
    validate_parser.add_argument('dirname', help='Root of directory to validate.')
    validate_parser.add_argument('template', help='Template file (yaml format).')
    validate_parser.set_defaults(func=validate)

    generate_parser = subparsers.add_parser('generate', help='Generate a template file from a target directory.')
    generate_parser.add_argument('dirname', help='Root of directory to validate.')
    generate_parser.add_argument('output', help='Output file (yaml format).')
    generate_parser.add_argument('--process-hidden', action="store_true", help="Don't skip hidden files and directories.")
    generate_parser.set_defaults(func=generate)
    
    return parser.parse_args()
     
def generate(args):
  # construct core template
  template = Template.construct(args.dirname, args.skip_hidden)

  # write to file
  with open(args.output, "w") as yamlfile:
    yaml.dump(template.dump(), yamlfile)
  print(f"Wrote extracted template from '{args.dirname}' to '{args.output}'")

def validate(args) -> bool:
  """ Validate the given directory against the given template. """
  template = Template.generate(args.templatefile)
  
  if (success := template.validate(args.dirname)):
    print(f"Directory {args.dirname} matches template {args.templatefile}")
  else:
    print(f"Directory {args.dirname} DOES NOT MATCH template {args.templatefile}")
  return success

def main():
  args = parse_args()
  args.func(args)
