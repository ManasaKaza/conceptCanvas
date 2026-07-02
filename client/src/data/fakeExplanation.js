export const examplePrompts = [
    "Explain recursion",
    "Explain database indexing",
    "Explain rate limiting",
    "Explain how transformers work",
];

export const fakeExplanation = {
    title: "Recursion",
    quickMeaning:
        "Recursion is when a function solves a problem by calling itself with a smaller version of the same problem.",
    steps: [
        "The function receives a problem.",
        "It checks if the problem is small enough to stop.",
        "If not, it calls itself with a smaller input.",
        "This continues until the base case is reached.",
        "Then the answers return back one by one.",
    ],
    analogy:
        "Think of Russian dolls. Each doll contains a smaller doll inside it until the smallest one is reached.",
    example:
        "factorial(3) = 3 × factorial(2) = 3 × 2 × factorial(1)",
    takeaways: [
        "Recursion means self-calling.",
        "Every recursion needs a base case.",
        "Without a base case, recursion can run forever.",
    ],
    followUps: ["What is a base case?", "What is call stack?", "Recursion vs loop?"],
};