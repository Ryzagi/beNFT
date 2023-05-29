import sqlite3


def delete_all_from_sql(sql_path: str):
    # Connect to the database
    conn = sqlite3.connect(sql_path)
    cursor = conn.cursor()

    # Delete all rows from the article table
    cursor.execute("DELETE FROM article")

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def get_info_from_sql(sql_path: str):
    # Connect to the database
    conn = sqlite3.connect(sql_path)
    cursor = conn.cursor()

    # Retrieve the text column from the article table
    cursor.execute("SELECT text FROM article")
    rows = cursor.fetchall()

    # Close the connection
    conn.close()

    # Process the rows and extract the text content
    texts = []
    for row in rows:
        texts.append(row[0])

    # Return the extracted text
    return texts


if __name__ == "__main__":
    print(get_info_from_sql("scrapper/articles.sqlite"))