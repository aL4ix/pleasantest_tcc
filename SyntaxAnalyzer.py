import pandas as pd


class SyntaxAnalyzer:
    def __init__(self, filepath):
        self.df = pd.read_csv(filepath, sep='\t', header=None, dtype=str)
        self.df.dropna(how='all', inplace=True)
        self.df.fillna('', inplace=True)
        self.table = self.df.values.tolist()
        self.current_line = 0
        self.syntax_tree = []

    def peek(self):
        if self.eof():
            return {'type': 'EOF'}
        row: list = self.table[self.current_line]
        return row

    def next(self):
        row = self.peek()
        self.current_line += 1
        return row

    def back(self):
        self.current_line -= 1

    def eof(self):
        return self.current_line >= len(self.table)

    @staticmethod
    def to_dict(row):
        return {row[1]: row[2]}

    @staticmethod
    def to_list(row):
        return row[1:3]

    @staticmethod
    def to_tuple(row):
        return tuple(row[1:3])

    def function(self, row):
        # print(f'SA: {row}')
        first, second = row[0:2]
        tree = {
            'type': first,
            'name': second,
            'parameters': {}
        }
        while not self.eof():
            first = self.peek()[0]
            if first == '':
                # FIXME if parameters repeat they will get overwritten
                tree['parameters'].update(self.to_dict(self.next()))
            elif first == 'steps':
                tree['function_steps'] = self.steps(self.next())
            else:
                break
        return tree

    def steps(self, row):
        # print(f'SA: {row}')
        tree = {
            'type': 'steps',
            'steps': []
        }
        self.back()
        while not self.eof():
            first = self.peek()[0]
            if first in ['', 'steps']:
                tree['steps'].append(self.step(self.next()))
            elif first == 'call':
                tree['steps'].append(self.call(self.next()))
            else:
                break
        return tree

    def step(self, row):
        # print(f'SA: {row}')
        node = {
            'type': 'step',
            'step': self.to_tuple(row)
        }
        return node

    def test_suite(self, row):
        # print(f'SA: {row}')
        first, second = row[0:2]
        extras = row[2:]
        tree = {
            'type': first,
            'suite_name': second,
            'test_cases': [],
            'extras': extras
        }
        while not self.eof():
            first = self.peek()[0]
            if first == 'test case':
                tree['test_cases'].append(self.test_case(self.next()))
            # if first == 'call':
            #    tree['call'].append(self.call(self.next()))
            else:
                break
        return tree

    def test_case(self, row):
        # print(f'SA: {row}')
        first, second = row[0:2]
        extras = row[2:]
        tree = {
            'type': first,
            'test_name': second,
            'extras': extras
        }
        while not self.eof():
            first = self.peek()[0]
            if first in ['steps', '', 'call']:
                tree['test_steps'] = self.steps(self.next())
            else:
                break
        return tree

    def call(self, row):
        # print(f'Start: {row}')
        first, second = row[0:2]
        tree = {
            'type': first,
            'call': second,
            'parameters': {}
        }
        while not self.eof():
            first = self.peek()[0]
            if first == '':
                # FIXME if parameters repeat they will get overwritten
                tree['parameters'].update(self.to_dict(self.next()))
            else:
                break
        return tree

    def analyse(self):
        switch = {'function': self.function,
                  'test suite': self.test_suite
                  }

        tree = []
        while not self.eof():
            row = self.next()
            line_number = self.current_line
            first = row[0]
            try:
                method_to_call = switch[first]
            except KeyError:
                raise SyntaxError(f'Error when compiling line {self.current_line} {row}')
            # noinspection PyArgumentList
            node = method_to_call(row)
            tree.append(node)
            # print(f'SA TREE: {node}')
            if line_number == self.current_line:
                raise RuntimeError(f'Syntax analyzer cycled infinitely at line {self.current_line} {row}')
        return tree
