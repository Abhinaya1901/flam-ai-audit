Ran the original script exactly as given:

python fertility.py - corpus english = eng_sample.txt -corpus hindi = hin_sample.txt -tokenizer gpt2

Output matched REPORT_v0.md exactly: english = 1.27, hindi = 7.45.
This confirms the report's numbers are reproducible from the script as it is.

Noticed eng_sample.txt line 7 has a double space:

"Please keep the books  in the cupboard."
Tested `line.split(" ")` in a Python shell:
Result: ['please', 'keep', 'the', 'books', '', 'in', 'the', 'cupboard.']
Finding: the double space produces an empty string '' counted as a "word",
increasing len(words) from 7  to 8 .

This makes fertility.py divide by an increased denominator on that line,
which understates true fertility.
Confirmed hin_sample.txt line 10 has the same issue
("किताबें  अलमारी" — double space).