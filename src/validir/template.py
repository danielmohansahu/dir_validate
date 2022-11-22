""" Class used to load, verify, and save directory templates.
"""

# future
from __future__ import annotations

# STL
import os
import typing
import functools
from collections import defaultdict
from operator import getitem

# YAML
import yaml

# Custom
from .types import Directory, File

def recursively_build_tree(node : [str, list, dict], result : [File, Dictionary], check_hidden : bool):
  # helper function to convert a dictionary of YAML keys to a linked tree structure
  if isinstance(node, str):
    if not (f := File.load(node)).hidden or check_hidden:
      result.children.append(f)
  elif isinstance(node, list):
    for item in node:
      recursively_build_tree(item, result, check_hidden)
  elif isinstance(node, dict):
    for key,val in node.items():
      if not (d := Directory.load(key)).hidden or check_hidden:
        result.children.append(d)
        recursively_build_tree(val, result.children[-1], check_hidden)
  else:
    raise KeyError("Encountered unexpected key type - only [str, list, dict] are supported.")

def recursively_compare_trees(nodes : Sequence[File, Directory], templates : Sequence[File, Directory], allow_extra : bool) -> bool:
  # verify that we have a match for all of our templates
  for template in templates:
    success = False
    for node in nodes:
      if node == template:
        # great! now check the children
        success = True if isinstance(node, File) else recursively_compare_trees(node.children, template.children, allow_extra)
    # check if we failed to find a particular template; this warrants exiting early
    if not success:
      print(f"Missing template item '{template.name}'!")
      return False

  # check if we want to also verify there aren't any extra files floating around
  if not allow_extra:
    for node in nodes:
      success = False
      for template in templates:
        if node == template:
          # great! now check the children
          success = True if isinstance(node, File) else recursively_compare_trees(node.children, template.children, allow_extra)
      # check if we failed to find a particular node; this warrants exiting early
      if not success:
        print(f"Found an extra object floating around: '{node.name}'")
        return False

  # success
  return True

class Template:
  def __init__(self, stream):
    # attempt to perform a pure yaml load
    self.root, self.check_hidden, self.allow_extra = self.load(stream)

  def validate(self, dirname : str) -> bool:
    """ Validate the given directory against our schema. """

    # load directory as its own tree
    other = Template.construct(dirname, self.check_hidden, self.allow_extra)

    # perform a deep comparison
    return recursively_compare_trees([other.root], [self.root], self.allow_extra)
    
  def dump(self) -> dict:
    """ Dump internal representation to a dictionary. """
    return self.root.dump()

  @staticmethod
  def load(stream : str):
    """ Convert a YAML representation into our internal data structure. """
    raw = yaml.safe_load(stream)

    # validate
    assert "root" in raw, "Missing required keyword 'root'."
    assert "flags" in raw, "Missing required keyword 'flags'."
    assert "check_hidden" in raw["flags"], "Missing required flag 'check_hidden'."
    assert "allow_extra" in raw["flags"], "Missing required flag 'allow_extra'."
    assert isinstance(raw["root"], list), "'root' key must be a list."

    # recursively convert to our internal tree representation
    root = Directory("root", False, [])
    recursively_build_tree(raw["root"], root, check_hidden)
    
    return root, check_hidden, allow_extra

  @staticmethod
  def construct(dirname : str, check_hidden : bool, allow_extra) -> Template:
    """ Factory method to construct from a directory.
    
    Args:
      dirname:      The directory to use as a template.
      check_hidden: Whether or not to consider hidden files.
      allow_extra:  Whether or not to consider extra files an error.
    """
    # extract all files via os.walk
    intermediary = {
      "flags": {
        "check_hidden": check_hidden,
        "allow_extra": allow_extra
      },
      "root": []
    }

    # walk through all directories / files
    for root, dirs, files in os.walk(dirname):

      # remove top level root directory and get list of sub-directories
      roots = root.replace(dirname, "", 1).split(os.sep)[1:]

      # get target node in our dictionary
      handle = intermediary["root"]
      for path in roots:
        handle = next(item[path] for item in handle if (isinstance(item, dict) and path in item))
      
      # naively add directories to their place in the hierarchy
      for directory in dirs:
        handle.append({directory : []})

      # add files based on our desired level of strictness
      for filename in files:
        handle.append(filename)

    # we dump this back into yaml format (which is kinda silly) and use nominal constructor
    return Template(yaml.dump(intermediary))