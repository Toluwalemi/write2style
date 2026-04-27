# Write2Style Evaluation Harness

Measures how well the Style DNA + RAG pipeline imitates a target author, by comparing generated drafts against held-out reference passages.

## Methodology

For each author the harness compares **three conditions** on the same prompts:

| Condition  | Style DNA | RAG (few-shot) |
|------------|-----------|----------------|
| `baseline` | no        | no             |
| `dna_only` | yes       | no             |
| `dna_rag`  | yes       | yes            |

Each generated output is graded by an **LLM-as-judge** (default model: `settings.style_model`) against the actual author's reference output for that prompt, on four 1–5 scales: `tone`, `vocabulary`, `structure`, `overall`. The overall score is the headline metric.

The harness is **offline by default** — it doesn't talk to Firestore, GCS, or Pinecone. Vectors are built in-memory with cosine similarity. The only external services it calls are OpenAI (embeddings) and OpenRouter (drafting + judging). This keeps eval cheap and reproducible.

## Data layout

```
eval/data/
└── <author_name>/
    ├── train_001.md     # any number of .md or .txt files used to build DNA + RAG
    ├── train_002.md
    ├── ...
    └── eval.json        # list of {prompt, reference} cases held out from training
```

`eval.json` schema:

```json
[
  {
    "prompt": "Write the opening paragraph of a blog post about debugging memory leaks.",
    "reference": "I lost three days to a memory leak last week. ..."
  }
]
```

The reference must be the actual author's writing for that prompt — not paraphrase.

## Running

```bash
cd backend
python -m eval.run                               # all authors, print to stdout
python -m eval.run --authors casual_tech         # restrict to one author
python -m eval.run --report ../eval-report.md    # save markdown
python -m eval.run --raw ../eval-raw.json        # also save raw scores
```

Cost: ~3 LLM calls per (author × case × condition) — one draft + one judge call per condition, plus embedding calls. For the bundled `casual_tech` author with 1 case × 3 conditions, expect a few cents on OpenRouter + a few thousand embedding tokens on OpenAI.

## Interpreting the table

- A working pipeline shows `dna_only > baseline` and `dna_rag ≥ dna_only`.
- If `dna_rag` is *worse* than `dna_only`, retrieval is hurting (likely irrelevant chunks dominating context). Investigate `top_k_few_shot`, chunk size, or the prompt's similarity to the training corpus.
- If `dna_only` ≈ `baseline`, the Style DNA prompt isn't biting. Check `prompts.STYLE_DNA_SYSTEM`, the model you're using, or whether your samples are too short/uniform to fingerprint.

## Adding authors

Drop a new directory under `data/` following the layout above. Aim for:

- 3–5 training samples, each at least a few hundred words, for a stable Style DNA
- 1–3 eval cases per author, with prompts the training samples don't cover verbatim
- References that are unmistakably *that author* — short excerpts (a paragraph or two) from their actual work
