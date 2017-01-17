# Copyright 2016  Mateusz Bysiek  http://mbdev.pl/
# This file is part of typed-astunparse.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tested function: dump."""

import ast
import logging
import unittest

import astunparse
import typed_ast.ast35
import typed_astunparse

from .examples import MODES, EXAMPLES, PATHS

_LOG = logging.getLogger(__name__)


def _postprocess_dump(tested_typed_dump):

    lines = [s.strip() for s in tested_typed_dump.splitlines()]
    lines = [s + ' ' if s.endswith(',') else s for s in lines]
    return ''.join(lines)


class DumpTests(unittest.TestCase):

    """Unit tests for dump() function."""

    def test_dump_examples(self):
        """Print ASTs of examples correctly."""
        for description, example in EXAMPLES.items():
            for mode in MODES:
                if example['trees'][mode] is None:
                    continue
                dump = typed_astunparse.dump(example['trees'][mode])
                _LOG.debug('%s', dump)
                dump = dump.replace('\n', '').replace(' ', '')
                self.assertEqual(dump, example['dumps'][mode], msg=(description, mode))

    def test_dump_files_comparison(self):
        """Print the same data as other existing modules."""
        for path in PATHS:
            with open(path, 'r', encoding='utf-8') as py_file:
                code = py_file.read()

            untyped_tree = ast.parse(source=code, filename=path)
            untyped_dump = astunparse.dump(untyped_tree)
            tested_untyped_dump = typed_astunparse.dump(untyped_tree)

            self.assertEqual(untyped_dump.splitlines(), tested_untyped_dump.splitlines())

            typed_tree = typed_ast.ast35.parse(source=code, filename=path)
            bad_typed_dump = astunparse.dump(typed_tree)

            for annotate_fields in [True, False]:
                for include_attributes in [False, True]:
                    if include_attributes and not annotate_fields:
                        continue # behaviour differs from typed_ast

                    with self.assertRaises(TypeError):
                        _ = typed_ast.ast35.dump(
                            untyped_tree, annotate_fields=annotate_fields,
                            include_attributes=include_attributes)

                    typed_dump = typed_ast.ast35.dump(
                        typed_tree, annotate_fields=annotate_fields,
                        include_attributes=include_attributes)
                    tested_typed_dump = _postprocess_dump(typed_astunparse.dump(
                        typed_tree, annotate_fields=annotate_fields,
                        include_attributes=include_attributes))

                    if include_attributes:
                        # because of https://github.com/python/typed_ast/issues/23
                        self.assertEqual(
                            typed_dump.replace(' ', ''), tested_typed_dump.replace(' ', ''))
                        continue
                    self.assertNotEqual(untyped_dump, bad_typed_dump)
                    self.assertNotEqual(typed_dump, bad_typed_dump)
                    self.assertEqual(typed_dump, tested_typed_dump)

    def test_many_dump_roundtrips(self):
        """Preserve ASTs after unparse(parse(...unparse(parse(dump(tree)))...))."""
        for description, example in EXAMPLES.items():
            for mode in MODES:
                if example['trees'][mode] is None:
                    continue

                dump = typed_astunparse.dump(example['trees'][mode])
                for _ in range(4):
                    tree = typed_ast.ast35.parse(source=dump, mode=mode)
                    dump = typed_astunparse.unparse(tree)
                    _LOG.debug('%s', dump)
                    clean_dump = dump.replace('\n', '').replace(' ', '')
                    self.assertEqual(clean_dump, example['dumps'][mode], msg=(description, mode))
                # TODO: use tree equality comparison below
                #tree = typed_ast.ast35.parse(source=dump, mode=mode)
                #self.assertTrue(typed_astunparse.equal(tree, example['trees'][mode]))
