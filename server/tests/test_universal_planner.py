import unittest

from app.storyboard_service import create_storyboard
from app.visual_strategy_service import plan_lesson


def explanation(title, steps, summary, details=None):
    return {
        "title": title,
        "quickMeaning": summary,
        "deepExplanation": summary,
        "stepByStep": steps,
        "realWorldExample": steps[-1],
        "analogy": "A simple analogy.",
        "technicalDetails": details or [],
        "commonConfusions": [],
        "interviewAngle": "Explain the core relationship clearly.",
        "summary": summary,
        "takeaways": [summary],
    }


CASES = [
    (
        "How does photosynthesis work?",
        explanation(
            "Photosynthesis",
            [
                "Chlorophyll absorbs light energy.",
                "Roots supply water to the leaves.",
                "Carbon dioxide enters through stomata.",
                "The reactions produce glucose and oxygen.",
            ],
            "Photosynthesis converts light, water, and carbon dioxide into stored chemical energy.",
        ),
        "natural_science",
        {"flow", "architecture", "sequence"},
    ),
    (
        "Show the timeline of the French Revolution",
        explanation(
            "French Revolution Timeline",
            [
                "Financial crisis weakened the monarchy.",
                "The Estates-General met in 1789.",
                "The Bastille was stormed.",
                "The republic replaced the monarchy.",
            ],
            "The revolution moved through connected political events over time.",
        ),
        "humanities",
        {"timeline"},
    ),
    (
        "Compare supply versus demand",
        explanation(
            "Supply and Demand",
            [
                "Supply describes how much producers offer.",
                "Demand describes how much buyers want.",
            ],
            "Price and quantity emerge from the interaction between supply and demand.",
        ),
        "social_science",
        {"comparison"},
    ),
    (
        "Explain kinetic energy using KE = 1/2 mv^2",
        explanation(
            "Kinetic Energy",
            [
                "Mass contributes linearly to kinetic energy.",
                "Speed contributes through its square.",
                "Doubling speed multiplies kinetic energy by four.",
            ],
            "Kinetic energy depends on mass and the square of speed.",
            ["KE = 1/2 mv^2"],
        ),
        "natural_science",
        {"formula"},
    ),
    (
        "Explain blood circulation as a cycle",
        explanation(
            "Blood Circulation",
            [
                "The heart pumps oxygenated blood to the body.",
                "Tissues use oxygen and return deoxygenated blood.",
                "The heart sends blood to the lungs.",
                "The lungs add oxygen before blood returns to the heart.",
            ],
            "Blood circulation continuously repeats through heart, body, and lungs.",
        ),
        "natural_science",
        {"cycle"},
    ),
    (
        "Trace how this algorithm executes",
        explanation(
            "Algorithm Execution",
            [
                "Read the input value.",
                "Evaluate the condition.",
                "Update the running result.",
                "Return the final output.",
            ],
            "The program changes state in a defined execution order.",
        ),
        "computing",
        {"code_execution"},
    ),
]


class UniversalPlannerTests(unittest.TestCase):
    def test_planner_selects_reusable_archetypes_across_domains(self):
        for question, content, expected_domain, expected_archetypes in CASES:
            with self.subTest(question=question):
                profile = plan_lesson(question, content)
                self.assertEqual(profile["subjectDomain"], expected_domain)
                self.assertIn(profile["primaryArchetype"], expected_archetypes)
                self.assertNotEqual(profile["primaryArchetype"], "fallback")

    def test_cross_domain_storyboards_validate_and_avoid_generic_nodes(self):
        for question, content, _, _ in CASES:
            with self.subTest(question=question):
                result = create_storyboard(
                    question=question,
                    explanation=content,
                    requested_scene_count=4,
                )
                self.assertEqual(result.storyboard["schemaVersion"], "2.1")
                self.assertEqual(len(result.storyboard["scenes"]), 4)
                self.assertTrue(result.storyboard["planningProfile"]["knowledgeShapes"])
                nodes = [
                    element
                    for scene in result.storyboard["scenes"]
                    for element in scene["visual"]["elements"]
                    if element["type"] == "node"
                ]
                self.assertTrue(nodes)
                self.assertFalse(any(node["nodeKind"] == "generic" for node in nodes))

    def test_visual_pipeline_has_no_topic_specific_dns_or_recursion_branch(self):
        from pathlib import Path

        source = Path(__file__).parents[1] / "app" / "visual_plan_service.py"
        text = source.read_text().lower()
        self.assertNotIn('family == "dns"', text)
        self.assertNotIn('family == "recursion"', text)
        self.assertNotIn("build_dns_visual", text)
        self.assertNotIn("build_recursion_visual", text)


if __name__ == "__main__":
    unittest.main()
