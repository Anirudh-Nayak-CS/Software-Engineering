import argparse

from services.pipeline import RequirementEngineeringPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate healthcare requirements and recommend an SDLC model."
    )
    parser.add_argument(
        "requirement",
        nargs="?",
        default=(
            "Build an AI-powered Hospital Management System that supports: "
            "Appointment Scheduling, Electronic Health Records, Doctor Dashboard, "
            "Patient Portal, AI Appointment Reminder, and Analytics Dashboard."
        ),
        help="The project requirement to analyze.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = RequirementEngineeringPipeline().run(args.requirement)

    print("--- GENERATED REQUIREMENT SPECIFICATION ---")
    print(result.requirement_specification)
    print("\n--- SDLC RECOMMENDATION ---")
    print(result.sdlc_recommendation)


if __name__ == "__main__":
    main()
