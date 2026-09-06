import tiktoken
import grapheme
from transformers import AutoTokenizer

# --- Load both tokenizers ---
gpt2_enc = tiktoken.get_encoding("gpt2")
xlmr_tok = AutoTokenizer.from_pretrained("xlm-roberta-base")

def gpt2_encode(s):
    return gpt2_enc.encode(s)

def xlmr_encode(s):
    return xlmr_tok.encode(s, add_special_tokens=False)

TOKENIZERS = {
    "gpt2": gpt2_encode,
    "xlm-roberta": xlmr_encode,
}

LANGS = ["eng", "hin", "tam", "tel"]

def load(path):
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

# Use devtest -- the held-out split reserved for final reported numbers
corpora = {lang: load(f"corpus_flores/{lang}_devtest.txt") for lang in LANGS}

def measure(lines, encode_fn):
    total_tokens = 0
    total_words = 0
    total_graphemes = 0
    total_bytes = 0
    total_sentences = len(lines)

    for line in lines:
        tokens = encode_fn(line)
        total_tokens += len(tokens)
        total_words += len(line.split())
        total_graphemes += grapheme.length(line)
        total_bytes += len(line.encode("utf-8"))

    return {
        "tok_per_word": total_tokens / total_words,
        "tok_per_grapheme": total_tokens / total_graphemes,
        "tok_per_byte": total_tokens / total_bytes,
        "tok_per_sentence": total_tokens / total_sentences,
    }

print(f"{'tokenizer':<14}{'lang':<6}{'tok/word':>10}{'tok/graph':>11}{'tok/byte':>11}{'tok/sent':>11}")
print("-" * 65)

results = {}
for tok_name, encode_fn in TOKENIZERS.items():
    for lang in LANGS:
        m = measure(corpora[lang], encode_fn)
        results[(tok_name, lang)] = m
        print(f"{tok_name:<14}{lang:<6}{m['tok_per_word']:>10.3f}{m['tok_per_grapheme']:>11.3f}"
              f"{m['tok_per_byte']:>11.4f}{m['tok_per_sentence']:>11.2f}")
    print()

# Ratios vs English, per tokenizer, per denominator
print("=== Ratios vs English ===")
for tok_name in TOKENIZERS:
    eng = results[(tok_name, "eng")]
    print(f"\n{tok_name}:")
    for lang in ["hin", "tam", "tel"]:
        r = results[(tok_name, lang)]
        print(f"  {lang}: word={r['tok_per_word']/eng['tok_per_word']:.2f}x  "
              f"graph={r['tok_per_grapheme']/eng['tok_per_grapheme']:.2f}x  "
              f"byte={r['tok_per_byte']/eng['tok_per_byte']:.2f}x  "
              f"sent={r['tok_per_sentence']/eng['tok_per_sentence']:.2f}x")