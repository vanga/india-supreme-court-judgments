import json
import html
from pathlib import Path
import pandas as pd

src_metadata_dir = "./data/metadata/raw"
csv_out_dir = "./data/metadata/clean"

metadata_files = list(Path(src_metadata_dir).glob("*.json"))
print(metadata_files)


def clean_df(df):
    for col in df.columns:
        df[col] = df[col].astype("string")
        df[col] = df[col].apply(lambda x: html.unescape(x) if pd.notnull(x) else x)
        df[col] = df[col].str.strip(" \n\t\r")
        df[col] = df[col].str.replace("\n\t\r", " ")
        # replace multiple spaces with single space
        df[col] = df[col].str.replace(" +", " ")
        # fill empty strings with NaN
        df[col] = df[col].replace("", pd.NA)
    return df


def process_judgment_links(df):
    df["temp_links"] = df["temp_link"].str.split("|")
    expl_df = df.explode("temp_links")
    expl_df["temp_link"] = clean_df(expl_df[["temp_links"]])
    expl_df = expl_df.drop(columns=["temp_links"])
    # assert all rows contain temp_link with .pdf
    assert expl_df["temp_link"].str.contains(".pdf").all()

    # strip anything after the string ".pdf" in the temp_link column
    expl_df["temp_link"] = expl_df["temp_link"].str.extract(r"(.+?\.pdf)", expand=False)
    # extract language
    expl_df["language"] = expl_df["temp_link"].str.extract(
        r"_([A-Z]+).pdf", expand=False
    )
    # assert all rows that have language to contain "vernacular" also in the temp_link column and vice versa
    assert (
        expl_df["language"].notnull() == expl_df["temp_link"].str.contains("vernacular")
    ).all(), "vernacular should be part of the url if language is present"

    return expl_df


all_df = pd.DataFrame()

for mf in metadata_files:
    with open(mf, "r") as f:
        fjson = json.load(f)
        df = pd.DataFrame.from_dict(fjson["data"])
        all_df = pd.concat([all_df, df], ignore_index=True)
all_df = clean_df(all_df)
all_df = process_judgment_links(all_df)
Path(csv_out_dir).mkdir(parents=True, exist_ok=True)
all_df.to_csv(Path(csv_out_dir) / "judgments.csv", index=False)
