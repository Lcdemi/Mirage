from InquirerPy.utils import get_style

matrix_style = get_style({
    "questionmark": "fg:#00FF00 bold",        # bright neon green
    "question": "fg:#00FF00 bold",
    "answer": "fg:#39FF14 bold",              # lime accent
    "pointer": "fg:#00FF00",                  # selection arrow
    "highlighted": "fg:#00FF00 bg:#003300",   # green text on dark green
    "selected": "fg:#ADFF2F",                 # yellow-green
    "separator": "fg:#006400",                # dark green line
    "instruction": "fg:#228B22",              # medium forest green
})

text_style = get_style({
    "questionmark": "fg:#00FF00 bold",       # neon green
    "answer": "fg:#39FF14 bold",             # your typed answer after submit
    "input": "fg:#00FF00",                   # text while typing
})