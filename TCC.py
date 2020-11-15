import os

import pandas as pd

import SyntaxAnalyzer


class TCC:
    def __init__(self):
        self.syn_nodes = []
        self.suite_table = {}

    def steps(self, steps_node, parameters_dict):
        result = []
        print(f'TCC: steps {steps_node}')
        print(f'TCC: steps params {parameters_dict}')
        for step_node in steps_node['steps']:
            print(f'TCC: steps step {step_node}')
            step_type = step_node['type']
            if step_type == 'step':
                test_step, expected = step_node['step']
                # FIXME add support to f-strings
                result.append((test_step.format(**parameters_dict), expected.format(**parameters_dict)))
            if step_type == 'call':
                result.extend(self.call_function(step_node))
        return result

    def call_function(self, call_node):
        result = []
        print(f'TCC: call {call_node}')
        parameters_dict = call_node['parameters']
        function_name = call_node['call']
        for syn_node in self.syn_nodes:
            syn_node_type = syn_node['type']
            if syn_node_type == 'function':
                if syn_node['name'] == function_name:
                    print(f'TCC: call function {syn_node}')
                    # FIXME add parameters validation
                    steps_node = syn_node['function_steps']
                    steps_table = self.steps(steps_node, parameters_dict)
                    result.extend(steps_table)
        return result

    def test_suite(self, suite_node):
        suite_name = suite_node['suite_name']
        self.suite_table = {'suite': suite_name,
                            'extras': suite_node['extras'],
                            'test_cases': []}
        for test_case_node in suite_node['test_cases']:
            case_name = test_case_node['test_name']
            case_extras = test_case_node['extras']
            print(f'TCC: suite tcn {test_case_node}')
            steps_node = test_case_node['test_steps']
            steps_table = self.steps(steps_node, {})
            self.suite_table['test_cases'].append({'test_case': case_name,
                                                   'extras': case_extras,
                                                   'steps': steps_table})
        print(f'TCC suite: {self.suite_table}')

    def compile(self, filepath):
        syn = SyntaxAnalyzer.SyntaxAnalyzer(filepath)
        self.syn_nodes = syn.analyse()
        for node in self.syn_nodes:
            print(f'TCC: compile node {node}')
            node_type = node['type']
            if node_type == 'function':
                continue
            elif node_type == 'test suite':
                self.test_suite(node)

    def export_to_csv(self, output_path):
        os.makedirs(output_path, exist_ok=True)
        representation = []
        suite_name = self.suite_table['suite']
        suite_path = os.path.join(output_path, f'{suite_name}.csv')
        suite_extras = self.suite_table['extras']
        test_cases = self.suite_table['test_cases']
        for test_case in test_cases:
            test_case_name = test_case['test_case']
            is_first_step = True
            steps = test_case['steps']
            extras = test_case['extras']
            for step in steps:
                if is_first_step:
                    is_first_step = False
                    first_column = test_case_name
                    last_columns = extras
                else:
                    first_column = ''
                    last_columns = []
                representation.append([first_column] + list(step) + last_columns)
        df = pd.DataFrame(representation, columns=['Test Case', 'Step', 'Expected Result'] + suite_extras, dtype=str)
        df.to_csv(suite_path, index=False)


if __name__ == '__main__':
    tcc = TCC()
    tcc.compile('test_cases_to_compile.csv')
    tcc.export_to_csv('output')
