from datasets import load_dataset
import os

LANG_COLS = {
    "eng": "sentence_eng_Latn",
    "hin": "sentence_hin_Deva",
    "tam": "sentence_tam_Taml",
    "tel": "sentence_tel_Telu",
}

os.makedirs("corpus_flores", exist_ok=True)

for split in ["dev", "devtest"]:
    print(f"Downloading split: {split}")
    ds = load_dataset("Muennighoff/flores200", "all", split=split, trust_remote_code=True)
    print("Columns available:", ds.column_names[:8], "...")

    for short_code, col in LANG_COLS.items():
        out_path = f"corpus_flores/{short_code}_{split}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            for row in ds:
                f.write(row[col].strip() + "\n")
        print(f"  {short_code}: {len(ds)} sentences -> {out_path}")

print("Done.")