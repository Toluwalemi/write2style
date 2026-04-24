type Props = {
  dna: Record<string, unknown> | null;
};

function asText(value: unknown): string {
  if (typeof value === "string") return value;
  if (value == null) return "";
  return JSON.stringify(value);
}

function asList(value: unknown): string[] {
  if (Array.isArray(value)) return value.map((v) => String(v));
  return [];
}

export function StyleDnaView({ dna }: Props) {
  if (!dna || Object.keys(dna).length === 0) {
    return <p className="empty">Upload a sample to generate a Style DNA.</p>;
  }

  const textFields: [string, string][] = [
    ["Tone", asText(dna.tone)],
    ["Sentence structure", asText(dna.sentence_structure)],
    ["Vocabulary", asText(dna.vocabulary)],
    ["Punctuation", asText(dna.punctuation)],
  ];

  const idioms = asList(dna.idioms);
  const doNot = asList(dna.do_not);

  return (
    <div className="dna-grid">
      {textFields.map(
        ([label, value]) =>
          value && (
            <div className="dna-item" key={label}>
              <h4>{label}</h4>
              <p>{value}</p>
            </div>
          )
      )}
      {idioms.length > 0 && (
        <div className="dna-item">
          <h4>Idioms</h4>
          <ul>
            {idioms.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}
      {doNot.length > 0 && (
        <div className="dna-item">
          <h4>Do not</h4>
          <ul>
            {doNot.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
