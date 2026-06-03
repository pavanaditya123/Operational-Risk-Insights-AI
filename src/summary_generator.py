def generate_summary(results, total_records, top_n=10):
    recurring_issues = [item for item in results if item["count"] > 1]

    return {
        "total_records_processed": total_records,
        "unique_keyphrases_found": len(results),
        "recurring_issues_found": len(recurring_issues),
        "top_issues": recurring_issues[:top_n],
    }
