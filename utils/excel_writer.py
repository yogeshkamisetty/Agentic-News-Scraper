import os
from datetime import datetime

import pandas as pd


def save_to_excel(articles):
    """
    Save articles to a timestamped Excel file.
    Returns None (and skips writing) if the article list is empty.
    """

    if not articles:
        return None

    os.makedirs("outputs", exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    output_path = f"outputs/agentic_updates_{timestamp}.xlsx"

    df = pd.DataFrame(articles)

    df.to_excel(output_path, index=False)

    return output_path