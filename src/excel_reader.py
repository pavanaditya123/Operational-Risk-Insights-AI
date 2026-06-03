import pandas as pd


class ExcelReader:
    def __init__(self, file_path, text_column=0, id_column=1):
        self.file_path = file_path
        self.text_column = text_column
        self.id_column = id_column

    def read_records(self):
        df = pd.read_excel(self.file_path, engine="openpyxl", header=None)

        required_column_count = max(self.text_column, self.id_column) + 1
        if df.shape[1] < required_column_count:
            raise ValueError(
                f"Expected at least {required_column_count} columns, found {df.shape[1]}"
            )

        for _, row in df.iterrows():
            text = row[self.text_column]
            record_id = row[self.id_column]

            if pd.isna(record_id) or pd.isna(text):
                continue

            yield {
                "record_id": self._format_record_id(record_id),
                "text": str(text).strip(),
            }

    def _format_record_id(self, record_id):
        if isinstance(record_id, float) and record_id.is_integer():
            return str(int(record_id))

        return str(record_id).strip()
