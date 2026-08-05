import { Moon, Sun } from "lucide-react";

function ThemeToggle({ theme, onToggle }) {
  const isDark = theme === "dark";
  return (
    <button type="button" onClick={onToggle} className="cc-icon-button" aria-label={isDark ? "Use light theme" : "Use dark theme"}>
      {isDark ? <Sun size={17} /> : <Moon size={17} />}
    </button>
  );
}

export default ThemeToggle;
