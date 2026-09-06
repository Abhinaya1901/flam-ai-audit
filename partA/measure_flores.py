import tiktoken

enc = tiktoken.get_encoding("gpt2")

def load(path):
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

eng_lines = load("corpus_flores/eng_dev.txt")
hin_lines = load("corpus_flores/hin_dev.txt")

def measure(lines, do_lower=True, split_fn=lambda s: s.split(" ")):
    ratios = []
    total_tok = 0
    total_words = 0
    for line in lines:
        if do_lower:
            line = line.lower()
        tokens = enc.encode(line)
        words = split_fn(line)
        ratios.append(len(tokens) / len(words))
        total_tok += len(tokens)
        total_words += len(words)
    macro = sum(ratios) / len(ratios)
    micro = total_tok / total_words
    return macro, micro

configs = {
    "baseline (original script logic)":      dict(do_lower=True,  split_fn=lambda s: s.split(" ")),
    "fixed split (bug 1 fix)":                dict(do_lower=True,  split_fn=lambda s: s.split()),
    "no lower (bug 2 fix)":                   dict(do_lower=False, split_fn=lambda s: s.split(" ")),
    "both fixes":                             dict(do_lower=False, split_fn=lambda s: s.split()),
}

print(f"{'config':<35}{'eng macro':>10}{'hin macro':>10}{'ratio':>8}{'  |  hin micro':>15}")
print("-" * 80)
for name, cfg in configs.items():
    eng_macro, eng_micro = measure(eng_lines, **cfg)
    hin_macro, hin_micro = measure(hin_lines, **cfg)
    ratio = hin_macro / eng_macro
    print(f"{name:<35}{eng_macro:>10.3f}{hin_macro:>10.3f}{ratio:>8.3f}{hin_micro:>15.3f}")