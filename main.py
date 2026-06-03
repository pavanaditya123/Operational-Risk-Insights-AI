from tqdm import tqdm
from src.excel_reader import ExcelReader
from src.cleaner import clean_text
from src.keyphrase_extractor import KeyphraseExtractor
from src.aggregator import PhraseAggregator
from src.summary_generator import generate_summary
from src.json_writer import write_json


INPUT_FILE = "data/test data(2).xlsx"
ANALYTICS_OUTPUT = "outputs/analytics.json"
SUMMARY_OUTPUT = "outputs/summary.json"


def main():
    reader = ExcelReader(INPUT_FILE)
    extractor = KeyphraseExtractor()
    aggregator = PhraseAggregator()

    total_records = 0
    for record in tqdm(reader.read_records(), desc="Processing records"):
        total_records += 1
        text = clean_text(record["text"])
        phrases = extractor.extract(text)
        aggregator.add(record["record_id"], phrases)

    analytics = aggregator.results(min_count=1)
    summary = generate_summary(results=analytics, total_records=total_records, top_n=10)

    write_json(analytics, ANALYTICS_OUTPUT)
    write_json(summary, SUMMARY_OUTPUT)

    print(f"Analytics saved to {ANALYTICS_OUTPUT}")
    print(f"Summary saved to {SUMMARY_OUTPUT}")


if __name__ == "__main__":
    main()
