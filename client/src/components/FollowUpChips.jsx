import { ArrowUpRight } from "lucide-react";

function FollowUpChips({ followUps, onFollowUpClick, disabled = false }) {
  return (
    <section className="cc-follow-ups">
      <p className="cc-eyebrow">Continue learning</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {followUps.map((item) => (
          <button
            type="button"
            key={item}
            onClick={() => onFollowUpClick(item)}
            disabled={disabled}
            className="cc-follow-up-button"
          >
            {item}
            <ArrowUpRight size={14} />
          </button>
        ))}
      </div>
    </section>
  );
}

export default FollowUpChips;
