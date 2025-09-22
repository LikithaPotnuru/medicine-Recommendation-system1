import mysql.connector

# --- Connect to MySQL ---
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="bvganapathi3600@gmail.com",  # Replace with your MySQL root password
    database="medicine_db"
)

cursor = conn.cursor()
print("Connection successful!")



import pandas as pd

# --- Load the CSV ---
df = pd.read_csv("cleaned_medicine_data.csv")  # make sure the CSV is in the same folder

# --- Replace all NaN with None for MySQL ---
df = df.where(pd.notnull(df), None)

print("CSV loaded successfully!")
print(df.head())




# --- Insert data into medicines table ---
for i, row in df.iterrows():
    sql = """
    INSERT INTO medicines
    (name, Chemical_Class, Therapeutic_Class, Action_Class, Habit_Forming, uses, side_effects, substitutes)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        row['name'],
        row['Chemical Class'],
        row['Therapeutic Class'],
        row['Action Class'],
        row['Habit Forming'],
        row['uses'],
        row['side_effects'],
        row['substitutes']
    )
    cursor.execute(sql, values)

# --- Commit changes and close ---
conn.commit()
print("CSV data inserted successfully!")

#cursor.close()
#conn.close()

# --- Search medicines ---
search_query = input("Enter medicine name or symptom to search: ").lower()

# Reopen cursor for search
cursor = conn.cursor()

# Search by medicine name or uses containing the query
sql = """
SELECT name, uses, substitutes
FROM medicines
WHERE LOWER(name) LIKE %s OR LOWER(uses) LIKE %s
LIMIT 10;
"""
like_query = f"%{search_query}%"
cursor.execute(sql, (like_query, like_query))

results = cursor.fetchall()

if results:
    print(f"\nTop results for '{search_query}':\n")
    for row in results:
        print("Name:", row[0])
        print("Uses:", row[1])
        print("Substitutes:", row[2])
        print("---------------------------")
else:
    print(f"No medicines found for '{search_query}'.")

cursor.close()
conn.close()

