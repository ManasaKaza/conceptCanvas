FAKE_EXPLANATIONS = {
    "recursion": {
        "title": "Recursion",
        "quickMeaning": (
            "Recursion is when a function solves a problem by calling itself "
            "with a smaller version of the same problem."
        ),
        "steps": [
            "The function receives a problem.",
            "It checks if the problem is small enough to stop.",
            "If not, it calls itself with a smaller input.",
            "This continues until the base case is reached.",
            "Then the answers return back one by one.",
        ],
        "analogy": (
            "Think of Russian dolls. Each doll contains a smaller doll inside it "
            "until the smallest one is reached."
        ),
        "example": "factorial(3) = 3 × factorial(2) = 3 × 2 × factorial(1)",
        "takeaways": [
            "Recursion means self-calling.",
            "Every recursion needs a base case.",
            "Without a base case, recursion can run forever.",
        ],
        "followUps": [
            "What is a base case?",
            "What is call stack?",
            "Recursion vs loop?",
        ],
    },
    "database indexing": {
        "title": "Database Indexing",
        "quickMeaning": (
            "A database index is a helper structure that allows the database to "
            "find rows faster without scanning the whole table."
        ),
        "steps": [
            "A table stores many rows of data.",
            "Without an index, the database may check many rows one by one.",
            "An index stores selected column values in a searchable structure.",
            "When a query uses that column, the database checks the index first.",
            "The index points the database to the matching rows faster.",
        ],
        "analogy": (
            "Think of a book index. Instead of reading every page, you look up a "
            "word in the index and jump directly to the right page."
        ),
        "example": "CREATE INDEX idx_users_email ON users(email);",
        "takeaways": [
            "Indexes speed up reads.",
            "Indexes can slow down writes because they must be updated.",
            "Indexes are useful on columns frequently used in WHERE, JOIN, or ORDER BY.",
        ],
        "followUps": [
            "How does B-tree index work?",
            "When should we avoid indexes?",
            "Index vs full table scan?",
        ],
    },
    "rate limiting": {
        "title": "Rate Limiting",
        "quickMeaning": (
            "Rate limiting controls how many requests a user or client can make "
            "within a specific time window."
        ),
        "steps": [
            "A user sends requests to the server.",
            "The rate limiter checks how many requests were already made.",
            "If the user is within the allowed limit, the request passes.",
            "If the user crosses the limit, the request is blocked.",
            "After the time window resets, the user can send requests again.",
        ],
        "analogy": (
            "Think of a ticket counter that allows only a certain number of people "
            "per minute so the counter does not get overloaded."
        ),
        "example": "Allow 100 requests per user per minute. Extra requests return 429 Too Many Requests.",
        "takeaways": [
            "Rate limiting protects backend systems.",
            "It prevents abuse and overload.",
            "Common algorithms include fixed window, sliding window, and token bucket.",
        ],
        "followUps": [
            "What is token bucket?",
            "What is 429 error?",
            "Rate limiting vs throttling?",
        ],
    },
    "transformers": {
        "title": "Transformers",
        "quickMeaning": (
            "Transformers are neural network architectures that understand relationships "
            "between words or tokens using attention."
        ),
        "steps": [
            "Text is split into tokens.",
            "Each token is converted into a numerical representation.",
            "Attention helps each token look at other important tokens.",
            "Multiple layers refine the meaning step by step.",
            "The model generates or predicts output based on learned patterns.",
        ],
        "analogy": (
            "Think of reading a sentence and deciding which words are most important "
            "to understand the meaning of each word."
        ),
        "example": "In 'The cat sat because it was tired', attention helps connect 'it' with 'cat'.",
        "takeaways": [
            "Transformers use attention.",
            "They process relationships between tokens.",
            "They are the foundation of many modern LLMs.",
        ],
        "followUps": [
            "What is attention?",
            "What are tokens?",
            "Transformer vs RNN?",
        ],
    },
}


GENERIC_EXPLANATION = {
    "title": "Concept Explanation",
    "quickMeaning": (
        "This concept can be understood by breaking it into smaller parts and "
        "looking at how each part works."
    ),
    "steps": [
        "Start with the basic meaning of the concept.",
        "Identify the main parts involved.",
        "Understand how those parts interact.",
        "Look at a simple example.",
        "Summarize the key takeaway.",
    ],
    "analogy": (
        "Think of it like learning how a machine works: first understand each part, "
        "then understand how the parts work together."
    ),
    "example": "A simple example will make the concept easier to connect with real life.",
    "takeaways": [
        "Break complex ideas into smaller parts.",
        "Use examples to understand better.",
        "Visual flow helps connect the steps.",
    ],
    "followUps": [
        "Explain this with an example",
        "Explain this visually",
        "Explain this like I am a beginner",
    ],
}