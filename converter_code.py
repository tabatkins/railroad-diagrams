import re
import sys

sys.stdout = open('converter_code.txt', 'w')

def parse_component(comp):
    # Check if it's a sequence like Y1~U~P
    if '~' in comp:
        parts = comp.split('~')
        head = parts[0]
        choices = ['~' + p for p in parts[1:]]
        return f"""Choice(0, Skip(),
           Sequence('{head}',
                    Choice(0, Skip(), {', '.join(f"'{c}'" for c in choices)}),)
           )"""
    else:
        return f"""Choice(0, Skip(),
           '{comp}',
           )"""

def convert_to_diagram(input_str):
    match = re.match(r'(\w+)\((.*)\)', input_str)
    if not match:
        raise ValueError("Input string is not in the expected format.")

    root, inner = match.groups()
    components = [c.strip() for c in inner.split(',')]

    diagram_parts = [f'Diagram(\n    "{root}("']
    for comp in components:
        diagram_parts.append('    ' + parse_component(comp) + ',')

    diagram_parts.append('    ")"\n)')
    return '\n'.join(diagram_parts)

# Example usage
input_str = "EGFR(ecd, tmd, Y1~U~P,Y2~U~P)"
output_code = convert_to_diagram(input_str)
print(output_code)

#test
input = 'Syk(tSH2,l~Y,a~Y)'
output_code = convert_to_diagram(input)
print('\n', output_code)

#test2
input_test2 = 'Syk()'
output_test2 = convert_to_diagram(input_test2)
print('\n', output_test2)

input_test3 = 'Rec(b~pY)'
output_test3 = convert_to_diagram(input_test3)
print('\n', output_test3)

