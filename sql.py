import sqlite3


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
