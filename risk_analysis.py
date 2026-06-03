import argparse
import os

from src.llm_risk_analyzer import analyze_risks, load_env_file, load_json, write_json


def parse_args():
    load_env_file()
    parser = argparse.ArgumentParser(description="Run LLM risk analysis on analytics.json")
    parser.add_argument("--input", default="outputs/analytics.json")
    parser.add_argument("--output", default="outputs/final_risk_summary.json")
    parser.add_argument("--chunk-size", type=int, default=25)
    parser.add_argument("--model", default=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--retry-delay", type=int, default=10)
    parser.add_argument("--include-not-risk", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    analytics = load_json(args.input)

    risks = analyze_risks(
        analytics=analytics,
        chunk_size=args.chunk_size,
        model=args.model,
        include_not_risk=args.include_not_risk,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay,
    )

    write_json(risks, args.output)
    print(f"Final risk summary saved to {args.output}")
    print(f"Risk items written: {len(risks)}")


if __name__ == "__main__":
    main()
