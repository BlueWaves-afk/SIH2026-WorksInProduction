import type { ActionCard as ActionCardModel } from "../../types";

export function ActionCardView({ card }: { card: ActionCardModel }) {
  return (
    <section className="surface panel" aria-label={card.title}>
      <div className="row"><div><p className="eyebrow">Approved action</p><h2>{card.title}</h2></div><span className="spacer" /><span className="band-chip green">v{card.version}</span></div>
      <div>
        {card.steps.map((step, index) => <div className="action-step" key={`${card.card_id}-${index}`}><span className="step-number">{index + 1}</span><span>{step.text}</span></div>)}
      </div>
      <p className="footer-note">Reviewed by {card.approved_by}. Sources: {card.source_refs.join(", ") || "approved action library"}.</p>
    </section>
  );
}
