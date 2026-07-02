function ThemeToggle({ theme, onToggle }) {
    const isDark = theme === "dark";

    return (
        <button
            onClick={onToggle}
            className="rounded-xl border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-700 shadow-sm hover:bg-gray-50"
        >
            {isDark ? "☀️ Light" : "🌙 Dark"}
        </button>
    );
}

export default ThemeToggle;