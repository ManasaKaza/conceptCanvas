import { ArrowUpRight } from "lucide-react";

function PromptCard({ prompt, onClick, disabled = false }) {
  return (
    <button
      type="button"
      onClick={() => onClick(prompt)}
      disabled={disabled}
      className="cc-prompt-suggestion group"
    >
      <span className="line-clamp-2">{prompt}</span>
      <ArrowUpRight size={14} className="shrink-0 opacity-45 transition group-hover:opacity-100" />
    </button>
  );
}

export default PromptCard;
